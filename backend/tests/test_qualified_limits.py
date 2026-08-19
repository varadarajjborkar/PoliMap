"""A limit and the ceiling stated on it are one rule.

    Room Rent Limit    1% of Sum Insured per day, subject to a maximum of
                       Rs. 5,000/- per day

is not two competing room limits. It is one entitlement, worth whichever of the
two binds lower against this policyholder's own cover, and the two figures have
to stay attached to each other until the compiler resolves them.

Extraction used to hand back the halves separately. The verification loop then
saw two room limits, concluded correctly that only one could be the term, and
resolved a contradiction that was never there by discarding half the rule. On a
₹3,00,000 cover it kept the ₹5,000 that never binds; on a ₹5,00,000 cover it
kept the 2% that the ₹7,500 caps. Both wrong, both confidently, and a wrong
room cap is not a wrong line on a summary: it sets the proportionate deduction
applied to the surgeon, theatre and nursing charges.

These tests hold the rule together at each place it could come apart: the
wording, the reading, the rejoining, and the rupees.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.pipeline.s2_atomize import patterns as P
from app.pipeline.s2_atomize.compose import fuse_qualified_limits
from app.schemas.document import Page, SourceMode
from app.schemas.policy import (
    Clause,
    ClauseKind,
    DocumentSection,
    Evidence,
    ExtractorKind,
    RoomLimit,
    RoomLimitBasis,
)

# --- the wording ----------------------------------------------------------

QUALIFIERS = [
    "1% of Sum Insured per day, subject to a maximum of Rs. 5,000/- per day",
    "1% of Sum Insured per day, subject to maximum of Rs. 5,000 per day",
    "1% of Sum Insured per day, capped at Rs. 5,000 per day",
    "1% of Sum Insured per day, subject to a cap of Rs. 5,000",
    "1% of Sum Insured per day, not exceeding Rs. 5,000 per day",
    "1% of Sum Insured per day but not exceeding Rs. 5,000",
    "1% of Sum Insured per day, not more than Rs. 5,000",
    "1% of Sum Insured per day, limited to Rs. 5,000 per day",
    "1% of Sum Insured per day, restricted to Rs. 5,000",
    "1% of Sum Insured per day, up to Rs. 5,000 per day",
    "1% of Sum Insured per day, up to a maximum of Rs. 5,000",
    "1% of Sum Insured per day or Rs. 5,000, whichever is lower",
    "1% of Sum Insured per day or Rs. 5,000, whichever is less",
    "1% of Sum Insured per day, max. Rs. 5,000",
]


@pytest.mark.parametrize("text", QUALIFIERS)
def test_every_way_of_saying_it_reads_as_one_capped_percentage(text):
    params = P.read_room_limit(text)
    assert params["basis"] == "pct_with_max", text
    assert params["pct_of_si"] == "1", text
    assert params["amount_inr"] == "5000", text


def test_a_bare_amount_is_not_a_capped_percentage():
    """No qualifier, no fusing. Two figures are two terms until stated otherwise."""
    assert P.read_room_limit("Rs. 5,000 per day")["basis"] == "flat"
    assert P.has_max_qualifier("Rs. 5,000 per day") is False


def test_a_bare_percentage_stays_a_bare_percentage():
    assert P.read_room_limit("1% of Sum Insured per day") == {
        "basis": "pct_of_si", "pct_of_si": "1"
    }


# --- the rupees -----------------------------------------------------------


@pytest.mark.parametrize(
    "sum_insured,pct,maximum,expected",
    [
        # The percentage binds: 1% of 3,00,000 is 3,000, under the 5,000 cap.
        (300000, 1, 5000, 3000),
        # The maximum binds: 2% of 5,00,000 is 10,000, over the 7,500 cap.
        (500000, 2, 7500, 7500),
        # Exactly equal, which must not depend on which side wins a tie.
        (500000, 1, 5000, 5000),
    ],
)
def test_the_lower_of_the_two_is_what_the_policy_pays(
    sum_insured, pct, maximum, expected
):
    limit = RoomLimit(
        basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
        pct_of_si=Decimal(pct),
        amount_per_day=Decimal(maximum),
    )
    assert limit.effective_daily_cap(Decimal(sum_insured)) == Decimal(expected)


def test_an_unread_cover_does_not_become_a_room_cap_of_nothing():
    """A percentage of an unknown cover is no cap, not a cap of zero.

    Taking the zero would tell somebody their entitlement is nothing, on a
    policy whose only real fault is that the cover figure was not read.
    """
    limit = RoomLimit(
        basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
        pct_of_si=Decimal(1),
        amount_per_day=Decimal(5000),
    )
    assert limit.effective_daily_cap(Decimal(0)) == Decimal(5000)


# --- the rejoining --------------------------------------------------------


def _clause(params, verbatim, *, page=0, section=DocumentSection.SCHEDULE,
            kind=ClauseKind.ROOM_RENT_CAP, confidence=0.8):
    return Clause(
        kind=kind,
        verbatim=verbatim,
        evidence=Evidence(page_index=page, section=section),
        params=params,
        confidence=confidence,
        extracted_by=ExtractorKind.MODEL,
    )


def _page(text: str) -> Page:
    return Page(
        page_index=0, width=600, height=800, text=text,
        source_mode=SourceMode.NATIVE, section=DocumentSection.SCHEDULE,
    )


SPLIT_SENTENCE = (
    "Room Rent Limit: 1% of Sum Insured per day, "
    "subject to a maximum of Rs. 5,000/- per day"
)


def test_halves_of_one_sentence_are_rejoined():
    pct = _clause({"basis": "pct_of_si", "pct_of_si": "1"},
                  "1% of Sum Insured per day")
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000/- per day")

    fused = fuse_qualified_limits([pct, flat], [_page(SPLIT_SENTENCE)])

    assert len(fused) == 1
    assert fused[0].params == {
        "basis": "pct_with_max", "pct_of_si": "1", "amount_inr": "5000",
        "per_day": True,
    }


def test_the_rejoined_clause_says_what_was_read_together():
    pct = _clause({"basis": "pct_of_si", "pct_of_si": "1"},
                  "1% of Sum Insured per day")
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000/- per day")
    fused = fuse_qualified_limits([pct, flat], [_page(SPLIT_SENTENCE)])
    assert any("Read together" in note for note in fused[0].notes)


def test_confidence_is_not_raised_by_rejoining():
    """Two halves of one reading are not two readings that agree."""
    pct = _clause({"basis": "pct_of_si", "pct_of_si": "1"},
                  "1% of Sum Insured per day", confidence=0.7)
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000/- per day", confidence=0.8)
    fused = fuse_qualified_limits([pct, flat], [_page(SPLIT_SENTENCE)])
    assert fused[0].confidence == pytest.approx(0.8)


def test_a_qualifier_in_the_quote_is_enough_on_its_own():
    """No page text needed when one of the quotes carries the wording itself."""
    pct = _clause(
        {"basis": "pct_of_si", "pct_of_si": "1"},
        "1% of Sum Insured per day, subject to a maximum of",
    )
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000/- per day")
    fused = fuse_qualified_limits([pct, flat], [_page("")])
    assert fused[0].params["basis"] == "pct_with_max"


# --- and what must never be rejoined --------------------------------------


def test_two_unrelated_limits_are_left_to_the_adjudicator():
    """Two figures with nothing tying them together are two claims, not one."""
    page = _page(
        "Room Rent Limit: 1% of Sum Insured per day.\n"
        "Room rent for the accompanying attendant: Rs. 5,000 per day."
    )
    pct = _clause({"basis": "pct_of_si", "pct_of_si": "1"},
                  "1% of Sum Insured per day")
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000 per day")
    assert len(fuse_qualified_limits([pct, flat], [page])) == 2


def test_a_room_limit_and_an_icu_limit_are_never_two_halves():
    pct = _clause({"basis": "pct_of_si", "pct_of_si": "1"},
                  "1% of Sum Insured per day, subject to a maximum of")
    icu = _clause({"basis": "flat", "amount_inr": "10000", "per_day": True},
                  "Rs. 10,000/- per day", kind=ClauseKind.ICU_CAP)
    assert len(fuse_qualified_limits([pct, icu], [_page("")])) == 2


def test_a_schedule_figure_and_a_wording_figure_stay_in_conflict():
    """That disagreement is real, and belongs to the adjudicator."""
    pct = _clause(
        {"basis": "pct_of_si", "pct_of_si": "1"},
        "1% of Sum Insured per day, subject to a maximum of",
        section=DocumentSection.SCHEDULE,
    )
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000/- per day", section=DocumentSection.WORDING)
    assert len(fuse_qualified_limits([pct, flat], [_page("")])) == 2


def test_figures_on_different_pages_stay_in_conflict():
    pct = _clause(
        {"basis": "pct_of_si", "pct_of_si": "1"},
        "1% of Sum Insured per day, subject to a maximum of", page=0,
    )
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000/- per day", page=1)
    assert len(fuse_qualified_limits([pct, flat], [_page("")])) == 2


def test_a_per_day_percentage_and_a_per_admission_ceiling_are_two_terms():
    pct = _clause(
        {"basis": "pct_of_si", "pct_of_si": "1", "per_day": True},
        "1% of Sum Insured per day, subject to a maximum of",
    )
    flat = _clause({"basis": "flat", "amount_inr": "50000", "per_day": False},
                   "Rs. 50,000 per admission")
    assert len(fuse_qualified_limits([pct, flat], [_page("")])) == 2


def test_a_sentence_break_between_them_is_not_one_sentence():
    page = _page(
        "Room Rent Limit: 1% of Sum Insured per day. "
        "Any room above the maximum of Rs. 5,000 per day attracts a deduction."
    )
    pct = _clause({"basis": "pct_of_si", "pct_of_si": "1"},
                  "1% of Sum Insured per day")
    flat = _clause({"basis": "flat", "amount_inr": "5000", "per_day": True},
                   "Rs. 5,000 per day")
    assert len(fuse_qualified_limits([pct, flat], [page])) == 2


def test_nothing_to_rejoin_leaves_the_ledger_untouched():
    only = _clause({"basis": "flat", "amount_inr": "6000", "per_day": True},
                   "Rs. 6,000 per day")
    assert fuse_qualified_limits([only], [_page("")]) == [only]


# --- and the figure has to be on the page ---------------------------------


def test_a_maximum_the_model_invented_never_reaches_the_ledger():
    """The condition field is written by the model, not copied from the page.

    Reading a ceiling out of it is worth doing, because a model asked for a
    limit and its condition separately will put the ceiling there. Reading it
    out of it *unchecked* would be the one thing this layer exists to prevent:
    a figure that never appeared in the document, entering the ledger with a
    grounded quote standing beside it, vouching for something it does not say.
    """
    from app.pipeline.s2_atomize.model_extract import ModelClause, _params_for

    page_text = "Room Rent Limit: 1% of Sum Insured per day"
    invented = ModelClause(
        kind="room_rent_cap",
        verbatim="1% of Sum Insured per day",
        value="1",
        unit="percent_of_sum_insured",
        condition="subject to a maximum of Rs. 5,000 per day",
    )
    params = _params_for(invented, page_text)
    assert params == {"basis": "pct_of_si", "pct_of_si": "1"}
    assert "amount_inr" not in params


def test_a_maximum_the_document_states_is_read_from_the_condition():
    from app.pipeline.s2_atomize.model_extract import ModelClause, _params_for

    page_text = (
        "Room Rent Limit: 1% of Sum Insured per day, "
        "subject to a maximum of Rs. 5,000 per day"
    )
    stated = ModelClause(
        kind="room_rent_cap",
        verbatim="1% of Sum Insured per day",
        value="1",
        unit="percent_of_sum_insured",
        condition="subject to a maximum of Rs. 5,000 per day",
    )
    params = _params_for(stated, page_text)
    assert params["basis"] == "pct_with_max"
    assert params["amount_inr"] == "5000"


# --- and end to end, clause to rupees --------------------------------------


@pytest.mark.parametrize(
    "sum_insured,pct,maximum,expected",
    [(300000, "1", "5000", 3000), (500000, "2", "7500", 7500)],
)
def test_a_composite_clause_compiles_to_the_binding_figure(
    sum_insured, pct, maximum, expected
):
    """The whole chain: what extraction produces, in rupees.

    These are the two policies in the corpus that used to come out wrong, and
    they fail in opposite directions, so a fix that simply always took the
    percentage or always took the maximum would pass one and fail the other.
    """
    from app.pipeline.s4_compile.compiler import _room_limit_from

    clause = _clause(
        {"basis": "pct_with_max", "pct_of_si": pct, "amount_inr": maximum,
         "per_day": True},
        f"{pct}% of Sum Insured per day, subject to a maximum of Rs. {maximum}",
    )
    limit = _room_limit_from(clause)
    assert limit.effective_daily_cap(Decimal(sum_insured)) == Decimal(expected)
