"""M5, triage and clause atomization.

The grounding tests carry the most weight. Grounding is the structural
guarantee that a language model cannot introduce a figure that does not exist
in the user's document, and it is enforced here in code rather than requested in
a prompt, so it needs to be held to that claim by tests that actually try to
smuggle inventions past it.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.pipeline.s2_atomize import grounding
from app.pipeline.s2_atomize import patterns as P
from app.pipeline.s2_atomize.atomize import merge
from app.pipeline.s2_atomize.grammar import (
    _confidence_for,
    _room_params,
    extract_page,
    find_labelled,
)
from app.schemas.document import Page, SourceMode
from app.schemas.policy import (
    Clause,
    ClauseKind,
    DocumentSection,
    Evidence,
    ExtractorKind,
)

SCHEDULE_TEXT = """SENTINEL HEALTH INSURANCE
POLICY SCHEDULE
Policy Number
SEN/2026/HLT/1234567
Policyholder Name
Vikram Iyer
SCHEDULE OF BENEFITS
Sum Insured (per policy year)
Rs. 5,00,000/-
Room Rent Limit
1% of Sum Insured per day, subject to a maximum of Rs. 5,000 per day
Intensive Care Unit (ICU) Limit
2% of Sum Insured per day
Co-payment
10% of each and every admissible claim
Pre-hospitalisation Expenses
30 days prior to admission
Post-hospitalisation Expenses
90 days from discharge
Non-Medical Consumables
Not covered. Refer Annexure of non-payable items.
PREMIUM DETAILS
Net Premium
Rs. 18,400
GST @ 18%
Rs. 3,312
Total Premium Paid
Rs. 21,712
"""


def make_page(text: str = SCHEDULE_TEXT, section=DocumentSection.SCHEDULE) -> Page:
    return Page(
        page_index=0, width=595, height=842, text=text,
        source_mode=SourceMode.NATIVE, section=section,
    )


# --- amount parsing -------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Rs. 5,00,000/-", 500000),
        ("₹5,00,000", 500000),
        ("INR 5,00,000", 500000),
        ("Rs. 5.00 Lakhs", 500000),
        ("Rupees Five Lakh Only", 500000),
        ("Rupees Twenty Five Lakh Only", 2500000),
        ("Rs. 1.5 Crore", 15000000),
        ("5 Lakh", 500000),
    ],
)
def test_indian_amount_notations(text, expected):
    assert P.parse_amount(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["Clause 5 applies", "page 12", "2026", "Sl. 1"])
def test_bare_numbers_are_not_money(text):
    # Clause numbers and years sit all over a policy; treating them as amounts
    # produces confident nonsense.
    assert P.parse_amount(text) is None


def test_amount_scan_skips_a_leading_percentage():
    """The regression that mattered most.

    Stopping at the first regex hit takes the "1" from "1%", fails the currency
    test, and reports the policy as having no rupee cap at all.
    """
    text = "1% of Sum Insured per day, subject to a maximum of Rs. 5,000 per day"
    assert P.parse_amount(text) == Decimal(5000)


def test_capped_amount_is_anchored_on_the_maximum_wording():
    text = "2% of Sum Insured per day, subject to a maximum of Rs. 7,500 per day"
    assert P.parse_capped_amount(text) == Decimal(7500)


def test_percent_of_sum_insured_requires_the_reference():
    assert P.parse_pct_of_sum_insured("1% of Sum Insured per day") == Decimal(1)
    # A bare percentage is not necessarily tied to the sum insured.
    assert P.parse_pct_of_sum_insured("10% co-payment") is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Single Private A/C Room", "single_private"),
        ("Twin Sharing Room", "twin_sharing"),
        ("General Ward", "general_ward"),
        ("Deluxe Room", "deluxe"),
        ("Suite", "suite"),
    ],
)
def test_room_categories(text, expected):
    assert P.parse_room_category(text) == expected


def test_no_limit_phrasings():
    for text in ("No sub-limit on room rent", "Not applicable", "Nil",
                 "Any room category permitted", "Covered up to Sum Insured"):
        assert P.states_no_limit(text), text


def test_durations():
    assert P.parse_months("24 months") == 24
    assert P.parse_months("3 years") == 36
    assert P.parse_days("30 days prior to admission") == 30


# --- room limit interpretation -------------------------------------------


def test_percentage_with_maximum_keeps_both_bounds():
    params = _room_params("1% of Sum Insured per day, subject to a maximum of Rs. 5,000")
    assert params == {
        "basis": "pct_with_max", "pct_of_si": "1", "amount_inr": "5000",
        "per_day": True,
    }


def test_plain_percentage():
    assert _room_params("1% of Sum Insured per day") == {
        "basis": "pct_of_si", "pct_of_si": "1"
    }


def test_flat_amount():
    params = _room_params("Rs. 6,000 per day")
    assert params["basis"] == "flat" and params["amount_inr"] == "6000"


def test_category_only():
    assert _room_params("Single Private Room entitlement")["category"] == "single_private"


def test_no_limit():
    assert _room_params("No sub-limit on room rent")["basis"] == "no_limit"


# --- table layout handling ------------------------------------------------


def test_label_finds_a_value_on_the_next_line():
    """Schedules are tables; read back as text the value lands below its label."""
    import re

    matches = find_labelled(
        SCHEDULE_TEXT, re.compile(r"Sum Insured", re.IGNORECASE),
        value_test=lambda t: P.parse_amount(t) is not None,
    )
    assert matches
    assert P.parse_amount(matches[0].value_text) == Decimal(500000)


def test_label_window_does_not_reach_the_next_row():
    import re

    text = "Room Rent Limit\n\n\n\nRs. 9,999 per day"
    assert not find_labelled(
        text, re.compile(r"Room Rent", re.IGNORECASE), window=2,
        value_test=lambda t: P.parse_amount(t) is not None,
    )


# --- grammar extraction ---------------------------------------------------


def _by_kind(clauses: list[Clause], kind: ClauseKind) -> Clause | None:
    found = [c for c in clauses if c.kind is kind]
    return max(found, key=lambda c: c.confidence) if found else None


@pytest.fixture(scope="module")
def schedule_clauses():
    return extract_page(make_page())


def test_sum_insured_is_read_not_the_premium(schedule_clauses):
    """The premium block sits right below the cover figure and looks similar."""
    clause = _by_kind(schedule_clauses, ClauseKind.SUM_INSURED)
    assert clause is not None
    assert clause.params["amount_inr"] == "500000"
    amounts = {c.params.get("amount_inr") for c in schedule_clauses}
    assert "18400" not in amounts and "21712" not in amounts


def test_room_and_icu_limits(schedule_clauses):
    room = _by_kind(schedule_clauses, ClauseKind.ROOM_RENT_CAP)
    assert room.params == {
        "basis": "pct_with_max", "pct_of_si": "1", "amount_inr": "5000",
        "per_day": True,
    }
    icu = _by_kind(schedule_clauses, ClauseKind.ICU_CAP)
    assert icu.params["pct_of_si"] == "2"


def test_copay_and_windows(schedule_clauses):
    assert _by_kind(schedule_clauses, ClauseKind.COPAY).params["pct"] == "10"
    assert _by_kind(schedule_clauses, ClauseKind.PRE_HOSPITALISATION).params["days"] == 30
    assert _by_kind(schedule_clauses, ClauseKind.POST_HOSPITALISATION).params["days"] == 90


def test_consumables_exclusion_is_read_as_not_covered(schedule_clauses):
    assert _by_kind(schedule_clauses, ClauseKind.CONSUMABLES_COVER).params["covered"] is False


def test_every_clause_quotes_text_that_exists_on_the_page(schedule_clauses):
    for clause in schedule_clauses:
        assert grounding.check(clause.verbatim, SCHEDULE_TEXT).grounded, clause.verbatim


# --- source authority -----------------------------------------------------


def test_wording_clauses_are_discounted():
    plain = _confidence_for(0.86, "Room Rent Limit Rs. 5,000 per day", DocumentSection.SCHEDULE)
    wording = _confidence_for(0.86, "Room Rent Limit Rs. 5,000 per day", DocumentSection.WORDING)
    assert wording < plain


def test_wording_that_defers_to_the_schedule_is_discounted_hard():
    """A default the customer may never have been sold must not be the answer."""
    hedged = _confidence_for(
        0.86,
        "Room rent entitlement under the standard plan is Rs. 2,000 per day "
        "unless otherwise specified in the Schedule",
        DocumentSection.WORDING,
    )
    assert hedged < 0.3


def test_a_schedule_clause_outranks_a_wording_clause():
    page = make_page(section=DocumentSection.SCHEDULE)
    wording_page = make_page(
        "Room Rent Limit\nRs. 2,000 per day", section=DocumentSection.WORDING
    )
    schedule = _by_kind(extract_page(page), ClauseKind.ROOM_RENT_CAP)
    wording = _by_kind(extract_page(wording_page), ClauseKind.ROOM_RENT_CAP)
    assert schedule.supersedes(wording)


# --- grounding ------------------------------------------------------------


def test_exact_and_whitespace_variant_quotes_pass():
    assert grounding.check("Room Rent Limit", SCHEDULE_TEXT).grounded
    assert grounding.check("Room   Rent\nLimit", SCHEDULE_TEXT).grounded


@pytest.mark.parametrize(
    "damaged",
    [
        "Sum Insured (per policy year) Rs. 5,OO,OOO/-",  # O for 0
        "maximum of Rs. S,000 per day",                  # S for 5
        "Co-payment 1O% of each and every admissible claim",
    ],
)
def test_ocr_damaged_quotes_still_ground(damaged):
    assert grounding.check(damaged, SCHEDULE_TEXT).grounded


@pytest.mark.parametrize(
    "invention",
    [
        "Room Rent Limit Rs. 9,999 per day",
        "Maternity benefit Rs. 50,000 per delivery",
        "Sum Insured Rs. 25,00,000",
        "the room rent limit is one percent of the sum insured",
    ],
)
def test_inventions_are_blocked(invention):
    """The guarantee: a figure absent from the document cannot reach the ledger."""
    result = grounding.check(invention, SCHEDULE_TEXT)
    assert not result.grounded, result


def test_a_quote_whose_digits_are_absent_is_rejected():
    # Words may be OCR-damaged; the figures may not simply be absent.
    result = grounding.check("Sum Insured (per policy year) Rs. 7,77,777/-", SCHEDULE_TEXT)
    assert not result.grounded


def test_short_quotes_are_refused_rather_than_guessed():
    assert not grounding.check("Rs.", SCHEDULE_TEXT).grounded
    assert not grounding.check("", SCHEDULE_TEXT).grounded


def test_grounding_returns_the_documents_own_wording():
    found = grounding.find_in_page("room rent limit", SCHEDULE_TEXT)
    assert found is not None and "Room Rent Limit" in found


# --- merging --------------------------------------------------------------


def _clause(kind, params, source, confidence=0.8, section=DocumentSection.SCHEDULE):
    return Clause(
        kind=kind, verbatim=f"quote for {params}",
        evidence=Evidence(page_index=0, section=section),
        params=params, confidence=confidence, extracted_by=source,
    )


def test_agreeing_extractors_merge_and_raise_confidence():
    """Independent agreement is evidence and should be recorded as such."""
    merged = merge([
        _clause(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, ExtractorKind.GRAMMAR, 0.80),
        _clause(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, ExtractorKind.MODEL, 0.65),
    ])
    assert len(merged) == 1
    assert merged[0].confidence > 0.80
    assert merged[0].notes


def test_disagreeing_extractors_are_both_kept():
    """Merging must not silently pick a winner; the adjudicator decides."""
    merged = merge([
        _clause(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, ExtractorKind.GRAMMAR),
        _clause(ClauseKind.SUM_INSURED, {"amount_inr": "1000000"}, ExtractorKind.MODEL),
    ])
    assert len(merged) == 2


def test_equal_amounts_written_differently_still_merge():
    merged = merge([
        _clause(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, ExtractorKind.GRAMMAR),
        _clause(ClauseKind.SUM_INSURED, {"amount_inr": "500000.00"}, ExtractorKind.MODEL),
    ])
    assert len(merged) == 1


def test_sublimits_on_different_heads_do_not_merge():
    merged = merge([
        _clause(ClauseKind.SUBLIMIT, {"amount_inr": "25000", "head": "investigations"},
                ExtractorKind.GRAMMAR),
        _clause(ClauseKind.SUBLIMIT, {"amount_inr": "25000", "head": "ambulance"},
                ExtractorKind.GRAMMAR),
    ])
    assert len(merged) == 2


# --- triage ---------------------------------------------------------------


def test_schedule_and_wording_are_told_apart():
    from app.pipeline.s1_triage.triage import classify_page

    schedule, _ = classify_page(make_page(SCHEDULE_TEXT, DocumentSection.UNKNOWN))
    assert schedule is DocumentSection.SCHEDULE

    wording_text = (
        "POLICY WORDING\n1. DEFINITIONS\nSum Insured means the maximum amount "
        "of cover available.\nThe Company shall not be liable for...\n"
        "GENERAL CONDITIONS\nCLAIM PROCEDURE"
    )
    wording, _ = classify_page(make_page(wording_text, DocumentSection.UNKNOWN))
    assert wording is DocumentSection.WORDING


def test_endorsement_outranks_schedule_precedence():
    assert DocumentSection.ENDORSEMENT.precedence > DocumentSection.SCHEDULE.precedence
    assert DocumentSection.SCHEDULE.precedence > DocumentSection.WORDING.precedence


def test_insurer_name_is_read_off_the_letterhead():
    from app.pipeline.s1_triage.triage import detect_insurer
    from app.schemas.document import IngestedDocument, InputKind

    doc = IngestedDocument(
        filename="p.pdf", input_kind=InputKind.PDF_TEXT, pages=[make_page()]
    )
    assert "Sentinel" in detect_insurer(doc)
