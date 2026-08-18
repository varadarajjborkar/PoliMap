"""Reading a hospital's final bill and checking it.

Discharge is the worst moment to read a bill for the first time, and it is the
only moment most people get. These test the two properties that make a check
worth putting in front of somebody at a counter: that it finds what is really
there, and that it stays quiet about what is not.

The second is the harder one. A checker that flags something on every bill gets
believed once. So the corpus carries bills with no planted fault at all, and the
arithmetic findings are gated on whether the document read cleanly enough to be
argued from, which is tested here directly.
"""

from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from app.bill import check, heads, nonpayable
from app.bill import read as reader
from app.schemas.bill import FindingKind, ReadBill
from app.schemas.document import (
    IngestedDocument,
    InputKind,
    Page,
    SourceMode,
)
from app.schemas.journey import AlertSeverity
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
)

CORPUS = Path("../data/generated/bills")


def a_document(text: str, *, native: bool = True) -> IngestedDocument:
    """A page carrying text but no word geometry, as a vision read produces."""
    return IngestedDocument(
        filename="bill.pdf",
        input_kind=InputKind.PDF_TEXT if native else InputKind.IMAGE,
        pages=[Page(
            page_index=0, width=595, height=842, text=text,
            source_mode=SourceMode.NATIVE if native else SourceMode.VISION,
        )],
    )


def a_policy(**kwargs) -> NormalizedPolicy:
    return NormalizedPolicy(sum_insured=D(500000), **kwargs)


# --- the IRDAI lists --------------------------------------------------------


@pytest.mark.parametrize("description, listing", [
    ("Gown", nonpayable.ItemList.OPTIONAL),
    ("ATTENDANT CHARGES", nonpayable.ItemList.OPTIONAL),
    ("Telephone Charges", nonpayable.ItemList.OPTIONAL),
    ("Shoe Cover", nonpayable.ItemList.IN_ROOM),
    ("Surgical Blade", nonpayable.ItemList.IN_PROCEDURE),
    ("Gauze", nonpayable.ItemList.IN_PROCEDURE),
    ("Admission Kit", nonpayable.ItemList.IN_TREATMENT),
    ("Sterillium 500ml", nonpayable.ItemList.IN_TREATMENT),
])
def test_listed_items_are_placed_on_the_right_list(description, listing):
    match = nonpayable.classify(description)
    assert match is not None, description
    assert match[1] is listing


@pytest.mark.parametrize("description", [
    "Oxygen Mask",
    "Nebuliser Mask",
    "PANTOP 40 MG CAPS",
    "Nursing Attendant Charges",
    "Gauze Dressing",
    "Room Rent - Single Private AC",
    "Surgeon's Professional Fee",
    "Inj. Ceftriaxone 1g",
])
def test_lexical_lookalikes_are_not_flagged(description):
    """A wrong flag sends somebody to argue over a charge that was correct,
    which costs them standing they will need for the ones that were not."""
    assert nonpayable.classify(description) is None


def test_subsumed_and_optional_are_different_things_to_say():
    """One is money to ask for back; the other is money that was always yours."""
    assert nonpayable.ItemList.IN_ROOM.is_subsumed
    assert not nonpayable.ItemList.OPTIONAL.is_subsumed
    assert "removed" in nonpayable.ItemList.IN_ROOM.ask
    assert "yours to pay" in nonpayable.ItemList.OPTIONAL.ask


# --- placing a line under a head --------------------------------------------


@pytest.mark.parametrize("description, head", [
    ("Room Rent - Single Private AC", ExpenseHead.ROOM_RENT),
    ("ICU Charges", ExpenseHead.ICU_CHARGES),
    ("ICU Nursing Charges", ExpenseHead.ICU_CHARGES),
    ("Nursing Charges", ExpenseHead.NURSING),
    ("Consultant Visit Charges", ExpenseHead.DOCTOR_VISIT),
    ("Surgeon's Professional Fee", ExpenseHead.SURGEON_FEE),
    ("Anaesthetist Fee", ExpenseHead.ANAESTHETIST_FEE),
    ("Operation Theatre Charges", ExpenseHead.OT_CHARGES),
    ("2D Echocardiography", ExpenseHead.INVESTIGATIONS),
    ("Inj. Pantoprazole 40mg", ExpenseHead.PHARMACY),
    ("Surgical Gloves", ExpenseHead.CONSUMABLES),
    ("Drug Eluting Stent", ExpenseHead.IMPLANTS),
    ("Oxygen Charges", ExpenseHead.OXYGEN),
    ("Registration Charges", ExpenseHead.NON_MEDICAL),
])
def test_a_line_is_placed_under_the_head_that_decides_how_it_settles(description, head):
    assert heads.head_of(description) is head


def test_a_blood_test_is_an_investigation_not_a_transfusion():
    """The word is the same and the head is not, and the head is what carries
    the proportionate deduction."""
    assert heads.head_of("Blood Grouping") is ExpenseHead.INVESTIGATIONS
    assert heads.head_of("Blood Transfusion Charges") is ExpenseHead.BLOOD


def test_a_line_nothing_places_is_left_unplaced():
    assert heads.head_of("Sundry") is None


# --- reading the document ---------------------------------------------------


def test_lines_come_off_the_page_with_their_figures():
    bill = reader.read(a_document(
        "Sr Particulars Qty Rate Amount\n"
        "1 Room Rent - Single Private AC 5 6,000 30,000\n"
        "2 Surgeon Fee 45,000\n"
        "Gross Total 75,000\n"
    ))
    assert [i.description for i in bill.items] == [
        "Room Rent - Single Private AC", "Surgeon Fee"
    ]
    assert bill.items[0].qty == D(5)
    assert bill.items[0].rate == D(6000)
    assert bill.items[0].amount == D(30000)
    assert bill.gross_total == D(75000)


def test_the_serial_number_is_not_part_of_the_item():
    bill = reader.read(a_document(
        "Sr Particulars Amount\n1 Nursing Charges 6,000\n"
    ))
    assert bill.items[0].description == "Nursing Charges"


def test_metadata_is_not_read_as_a_charge():
    """Without this, "Bill No 3412" is a charge of three thousand rupees."""
    bill = reader.read(a_document(
        "Bill No 3412\nUHID 998877\nAge 61\n"
        "Sr Particulars Amount\n1 Nursing Charges 6,000\n"
    ))
    assert [i.description for i in bill.items] == ["Nursing Charges"]


def test_an_admission_kit_is_a_charge_and_an_admission_date_is_not():
    bill = reader.read(a_document(
        "Sr Particulars Amount\n"
        "1 Admission Kit 650\n"
        "Admission Date 12 08 2026\n"
    ))
    assert [i.description for i in bill.items] == ["Admission Kit"]


def test_a_section_banner_places_the_lines_beneath_it():
    """Bills are laid out in sections, and a line under a pharmacy banner is
    pharmacy whatever the hospital chose to call it."""
    bill = reader.read(a_document(
        "Sr Particulars Amount\n"
        "PHARMACY CHARGES\n"
        "1 Sundry item 400\n"
    ))
    assert bill.items[0].head is ExpenseHead.PHARMACY
    assert bill.items[0].from_section


def test_totals_are_read_as_totals_rather_than_as_lines():
    bill = reader.read(a_document(
        "Sr Particulars Amount\n"
        "1 Nursing Charges 6,000\n"
        "Gross Total 6,000\n"
        "Less: Discount 500\n"
        "Less: Advance Paid 2,000\n"
        "Net Payable 3,500\n"
    ))
    assert len(bill.items) == 1
    assert bill.gross_total == D(6000)
    assert bill.discount == D(500)
    assert bill.advance_paid == D(2000)
    assert bill.net_payable == D(3500)


def test_a_document_with_no_table_says_so_rather_than_returning_nothing():
    bill = reader.read(a_document("DISCHARGE SUMMARY\nPatient did well.\n"))
    assert not bill.items
    assert any("could not find a table" in note for note in bill.notes)


def test_the_lines_are_checked_against_the_bills_own_total():
    reconciling = reader.read(a_document(
        "Sr Particulars Amount\n1 Nursing 6,000\nGross Total 6,000\n"
    ))
    assert reconciling.reconciles

    drifting = reader.read(a_document(
        "Sr Particulars Amount\n1 Nursing 6,000\nGross Total 9,000\n"
    ))
    assert not drifting.reconciles


# --- checking it ------------------------------------------------------------


def a_bill(text: str, *, native: bool = True) -> ReadBill:
    return reader.read(a_document(text, native=native))


def kinds_of(review) -> set[FindingKind]:
    return {f.kind for f in review.findings}


def test_an_item_the_regulator_places_inside_the_room_charge_is_raised():
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Room Rent - General Ward 4,000\n"
        "2 Shoe Cover 120\n"
        "Gross Total 4,120\n"
    ), a_policy())
    subsumed = next(f for f in review.findings if f.kind is FindingKind.SUBSUMED)
    assert subsumed.amount == D(120)
    assert "removed" in subsumed.ask
    assert subsumed.lines == [2]


def test_an_item_no_policy_pays_is_named_without_being_called_a_mistake():
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Nursing Charges 4,000\n"
        "2 Telephone Charges 180\n"
        "Gross Total 4,180\n"
    ), a_policy())
    optional = next(f for f in review.findings if f.kind is FindingKind.OPTIONAL_ITEM)
    assert optional.severity is AlertSeverity.INFO
    assert "yours to pay" in optional.ask


def test_a_line_that_does_not_multiply_out_is_raised_with_both_figures():
    review = check.review(a_bill(
        "Sr Particulars Qty Rate Amount\n"
        "1 Consultant Visit 6 500 2,500\n"
        "Gross Total 2,500\n"
    ), a_policy())
    finding = next(f for f in review.findings if f.kind is FindingKind.LINE_ARITHMETIC)
    assert "3,000" in finding.headline
    assert "2,500" in finding.headline


def test_lines_that_do_not_add_up_to_the_total_are_raised():
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Nursing Charges 4,000\n"
        "2 Surgeon Fee 20,000\n"
        "Gross Total 26,000\n"
    ), a_policy())
    finding = next(f for f in review.findings if f.kind is FindingKind.TOTAL_MISMATCH)
    assert finding.severity is AlertSeverity.URGENT
    assert finding.amount == D(2000)


def test_a_bill_that_prints_its_total_after_discount_is_not_accused():
    """Some hospitals print the discounted figure as the gross. That is a naming
    convention, not a discrepancy."""
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Nursing Charges 5,000\n"
        "Gross Total 4,500\n"
        "Less: Discount 500\n"
    ), a_policy())
    assert FindingKind.TOTAL_MISMATCH not in kinds_of(review)


def test_the_same_line_twice_is_asked_about_rather_than_alleged():
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Operation Theatre Charges 8,000\n"
        "2 Operation Theatre Charges 8,000\n"
        "Gross Total 16,000\n"
    ), a_policy())
    finding = next(f for f in review.findings if f.kind is FindingKind.DUPLICATE)
    assert finding.amount == D(8000)
    assert "Ask whether" in finding.ask


def test_a_clean_bill_raises_nothing_worth_arguing_about():
    review = check.review(a_bill(
        "Sr Particulars Qty Rate Amount\n"
        "1 Room Rent - General Ward 2 2,000 4,000\n"
        "2 Nursing Charges 2 500 1,000\n"
        "3 Surgeon Fee 20,000\n"
        "Gross Total 25,000\n"
    ), a_policy())
    assert review.questionable == D(0)
    assert not {
        FindingKind.SUBSUMED, FindingKind.DUPLICATE,
        FindingKind.LINE_ARITHMETIC, FindingKind.TOTAL_MISMATCH,
    } & kinds_of(review)


def test_lines_that_could_not_be_placed_are_declared_not_guessed():
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Sundry 900\n"
        "Gross Total 900\n"
    ), a_policy())
    finding = next(f for f in review.findings if f.kind is FindingKind.UNPLACED)
    assert finding.amount == D(900)


# --- a photograph we could not read -----------------------------------------


def test_a_photograph_that_does_not_reconcile_says_so_instead_of_accusing():
    """A misread digit turns an ordinary bill into a discrepancy that does not
    exist, and the family spends its one conversation on our mistake."""
    review = check.review(a_bill(
        "Sr Particulars Qty Rate Amount\n"
        "1 Nursing Charges 5 500 131,924\n"
        "Gross Total 2,500\n",
        native=False,
    ), a_policy())
    assert FindingKind.UNCERTAIN_READ in kinds_of(review)
    assert FindingKind.TOTAL_MISMATCH not in kinds_of(review)
    assert FindingKind.LINE_ARITHMETIC not in kinds_of(review)


def test_a_photograph_that_reconciles_is_checked_like_any_other_bill():
    """The printed total is a checksum over the lines. A photograph that
    reproduces it was read correctly, whatever the recognition score says."""
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 Nursing Charges 5,000\n"
        "2 Gauze 320\n"
        "Gross Total 5,320\n",
        native=False,
    ), a_policy())
    assert FindingKind.UNCERTAIN_READ not in kinds_of(review)
    assert FindingKind.SUBSUMED in kinds_of(review)


# --- what the policy will do to it ------------------------------------------


def test_the_room_cap_and_its_knock_on_are_raised_off_the_bills_own_room_rate():
    policy = a_policy(room_limit=RoomLimit(
        basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(5000)
    ))
    review = check.review(a_bill(
        "Sr Particulars Qty Rate Amount\n"
        "1 Room Rent - Single Private Room 5 8,000 40,000\n"
        "2 Nursing Charges 5 1,000 5,000\n"
        "3 Surgeon Fee 60,000\n"
        "Gross Total 105,000\n"
    ), policy)

    assert FindingKind.ROOM_ABOVE_CAP in kinds_of(review)
    proportionate = next(
        f for f in review.findings if f.kind is FindingKind.PROPORTIONATE
    )
    assert "May 2024" in proportionate.ask
    assert proportionate.severity is AlertSeverity.URGENT


def test_the_settlement_is_the_same_engine_the_estimate_used():
    """Two views of one arithmetic, so a family quoted one figure and handed
    another can see which line moved."""
    review = check.review(a_bill(
        "Sr Particulars Qty Rate Amount\n"
        "1 Room Rent - General Ward 2 2,000 4,000\n"
        "2 Surgeon Fee 20,000\n"
        "Gross Total 24,000\n"
    ), a_policy())
    assert review.settlement is not None
    assert review.settlement.reconciles()
    assert review.settlement.gross_total == D(24000)


def test_the_room_tier_is_read_off_the_bill_when_nobody_says_what_it_was():
    bill = a_bill(
        "Sr Particulars Qty Rate Amount\n"
        "1 Room Rent - Twin Sharing 3 2,000 6,000\n"
        "Gross Total 6,000\n"
    )
    review = check.review(bill, a_policy())
    assert review.settlement is not None
    assert review.settlement.room_category is RoomCategory.TWIN_SHARING


def test_consumables_are_named_as_the_families_own_cost():
    review = check.review(a_bill(
        "Sr Particulars Amount\n"
        "1 IV Cannula 18G 600\n"
        "Gross Total 600\n"
    ), a_policy())
    finding = next(f for f in review.findings if f.kind is FindingKind.CONSUMABLES)
    assert finding.amount == D(600)


def test_a_bill_with_nothing_readable_on_it_is_not_settled_at_all():
    review = check.review(a_bill("DISCHARGE SUMMARY\nPatient did well.\n"), a_policy())
    assert review.settlement is None


# --- against the corpus -----------------------------------------------------


def corpus_bills() -> list[dict]:
    manifest = CORPUS / "manifest.json"
    if not manifest.exists():
        pytest.skip("bill corpus not built")
    return json.loads(manifest.read_text())["bills"]


FAULT_FINDINGS = {
    "subsumed_item": FindingKind.SUBSUMED,
    "duplicate_line": FindingKind.DUPLICATE,
    "line_arithmetic": FindingKind.LINE_ARITHMETIC,
    "total_mismatch": FindingKind.TOTAL_MISMATCH,
}


@pytest.fixture(scope="module")
def reviewed() -> list[tuple[dict, ReadBill, object]]:
    """Every bill in the corpus, read and checked once."""
    from app.pipeline.s0_intake.intake import ingest

    out = []
    for entry in corpus_bills():
        truth = json.loads((CORPUS.parent / entry["truth_path"]).read_text())
        document = CORPUS.parent / entry["documents"][0]["path"]
        bill = reader.read(ingest(document))
        out.append((truth, bill, check.review(bill, a_policy())))
    return out


def test_every_line_on_every_bill_is_read(reviewed):
    for truth, bill, _ in reviewed:
        assert len(bill.items) == len(truth["lines"]), truth["bill_id"]
        assert str(bill.line_total) == truth["line_total"], truth["bill_id"]


def test_every_line_is_placed_under_the_head_it_was_generated_as(reviewed):
    for truth, bill, _ in reviewed:
        for item, want in zip(bill.items, truth["lines"], strict=True):
            if want["head"] is None:
                continue
            assert item.head is not None and item.head.value == want["head"], (
                f"{truth['bill_id']} line {item.line_no}: {item.description}"
            )


def test_every_planted_fault_is_found(reviewed):
    for truth, _, review in reviewed:
        raised = {f.kind for f in review.findings}
        for fault in truth["planted"]:
            assert FAULT_FINDINGS[fault] in raised, f"{truth['bill_id']}: {fault}"


def test_nothing_is_raised_that_was_not_planted(reviewed):
    """Precision. A checker that finds something wrong with every bill is one
    nobody believes the second time."""
    for truth, _, review in reviewed:
        expected = {FAULT_FINDINGS[f] for f in truth["planted"]}
        raised = {f.kind for f in review.findings} & set(FAULT_FINDINGS.values())
        assert raised == expected, f"{truth['bill_id']}: {raised} vs {expected}"


def test_some_of_the_corpus_carries_no_fault_at_all(reviewed):
    assert sum(1 for truth, _, _ in reviewed if not truth["planted"]) >= 3
