"""Checking a hospital bill against the policy and the regulator's own list.

Discharge is the worst moment to read a bill for the first time. The family has
been awake for days, the ward wants the bed, and the figure at the bottom is
presented as arithmetic that has already happened. In practice a fair number of
lines on it are negotiable, and the ones that are follow rules anybody can
check: an item the IRDAI schedule places inside the room charge should not also
appear beside it, a quantity times a rate should come to the amount charged, and
the lines should add up to the total.

The findings are therefore written as things to say rather than things to know.
Each carries the rupees, the lines it came from, and one sentence that can be
read out at a counter. Nothing here accuses anybody of anything: hospital
billing is done at speed by people with several hundred lines to enter, and
"could you check this line" gets a bill corrected where an accusation gets a
supervisor.

The settlement at the end is the same waterfall the estimate used, run on the
real bill. That is deliberate. A family quoted one figure before admission and
handed another at discharge can put the two side by side and see which line
moved, which no separate piece of arithmetic would let them do.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.bill import nonpayable
from app.core.logging import get_logger
from app.pipeline.s2_atomize.patterns import parse_room_category
from app.pipeline.s6_simulate import waterfall
from app.schemas.bill import (
    BilledItem,
    BillFinding,
    BillReview,
    FindingKind,
    ReadBill,
)
from app.schemas.journey import AlertSeverity
from app.schemas.money import ZERO, format_inr, round_inr
from app.schemas.policy import ExpenseHead, NormalizedPolicy, RoomCategory
from app.schemas.simulation import (
    BillLine,
    DeductionKind,
    EstimatedBill,
    SimulationResult,
)

log = get_logger(__name__)

PENNY = Decimal("1")
"""Rounding tolerance. Bills are printed in whole rupees; a rupee either way is
the printer, not a mistake worth anybody's afternoon."""


def review(
    bill: ReadBill,
    policy: NormalizedPolicy,
    *,
    hospital_name: str = "",
    hospital_id: str = "",
    procedure_code: str = "",
    room_category: RoomCategory | None = None,
    is_network: bool = True,
    patient_age: int | None = None,
) -> BillReview:
    """Check a bill that has been read, against the policy behind it."""
    findings: list[BillFinding] = []
    findings.extend(_listed_items(bill))
    findings.extend(_duplicates(bill))
    if _arithmetic_is_worth_checking(bill):
        findings.extend(_line_arithmetic(bill))
        findings.extend(_totals(bill))
    else:
        findings.append(_uncertain(bill))
    findings.extend(_unplaced(bill))

    settlement = None
    if bill.placed:
        settlement = _settle(
            bill, policy,
            hospital_name=hospital_name, hospital_id=hospital_id,
            procedure_code=procedure_code, room_category=room_category,
            is_network=is_network, patient_age=patient_age,
        )
        findings.extend(_from_settlement(settlement, bill, policy))

    findings.sort(key=lambda f: (-f.severity.rank, -float(f.amount)))
    log.info(
        "checked a bill",
        lines=len(bill.items),
        findings=len(findings),
        total=str(bill.line_total),
    )
    return BillReview(bill=bill, findings=findings, settlement=settlement)


# --- what the bill says about itself ----------------------------------------


def _arithmetic_is_worth_checking(bill: ReadBill) -> bool:
    """Whether the figures are solid enough to argue arithmetic from.

    A document read off its own text layer is exact. A photograph is not, and a
    single misread digit turns an ordinary bill into a fifty thousand rupee
    discrepancy that does not exist. The test is the bill's own total: it is a
    checksum over the lines, so a photograph whose lines reproduce it was read
    correctly, and one that does not was not. Telling somebody at a counter that
    their total is wrong when it is our reading that is wrong costs them the
    standing they need for the lines that really are wrong.
    """
    return bill.from_text_layer or bill.reconciles


def _uncertain(bill: ReadBill) -> BillFinding:
    return BillFinding(
        kind=FindingKind.UNCERTAIN_READ,
        severity=AlertSeverity.ATTENTION,
        headline="We could not read every figure on this photograph",
        detail=(
            f"The lines we read come to {format_inr(bill.line_total)}"
            + (
                f", and the bill's own total says {format_inr(bill.gross_total)}."
                if bill.gross_total is not None
                else ", and we could not find the bill's own total."
            )
            + " Those should agree, so at least one figure has been read wrong."
        ),
        ask="Check the lines below against the paper before using any of them. "
            "A photograph taken square-on in good light, or the PDF the billing "
            "desk can email you, reads exactly.",
        amount=ZERO,
        lines=[],
    )




def _listed_items(bill: ReadBill) -> list[BillFinding]:
    """Lines the IRDAI schedule says should not be there, or are not payable."""
    grouped: dict[nonpayable.ItemList, list[BilledItem]] = defaultdict(list)
    for item in bill.items:
        if (match := nonpayable.classify(item.description)) is not None:
            grouped[match[1]].append(item)

    findings: list[BillFinding] = []
    for listing, items in grouped.items():
        total = round_inr(sum((i.amount for i in items), ZERO))
        findings.append(BillFinding(
            kind=(
                FindingKind.SUBSUMED if listing.is_subsumed
                else FindingKind.OPTIONAL_ITEM
            ),
            severity=(
                AlertSeverity.ATTENTION if listing.is_subsumed else AlertSeverity.INFO
            ),
            headline=f"{_names(items)}: {format_inr(total)}",
            detail=listing.label + ".",
            ask=listing.ask,
            amount=total,
            lines=[i.line_no for i in items],
        ))
    return findings


def _duplicates(bill: ReadBill) -> list[BillFinding]:
    """The same line entered more than once.

    Phrased as a question rather than a finding, because the same medicine at
    the same price on two days of a stay is an ordinary bill and not a mistake.
    """
    seen: dict[tuple[str, Decimal], list[BilledItem]] = defaultdict(list)
    for item in bill.items:
        seen[(nonpayable.normalise(item.description), item.amount)].append(item)

    findings: list[BillFinding] = []
    for (_, amount), items in seen.items():
        if len(items) < 2:
            continue
        extra = round_inr(amount * (len(items) - 1))
        findings.append(BillFinding(
            kind=FindingKind.DUPLICATE,
            severity=AlertSeverity.ATTENTION,
            headline=f"{items[0].description} appears {len(items)} times, "
                     f"{format_inr(amount)} each",
            detail=f"Lines {', '.join(str(i.line_no) for i in items)}.",
            ask="Ask whether this was entered twice. The same charge on two "
                "different days is normal, so the answer may well be yes it is "
                "right, but it costs nothing to ask.",
            amount=extra,
            lines=[i.line_no for i in items],
        ))
    return findings


def _line_arithmetic(bill: ReadBill) -> list[BillFinding]:
    findings: list[BillFinding] = []
    for item in bill.items:
        if item.qty is None or item.rate is None:
            continue
        expected = round_inr(item.qty * item.rate)
        if abs(expected - item.amount) <= PENNY:
            continue
        difference = item.amount - expected
        findings.append(BillFinding(
            kind=FindingKind.LINE_ARITHMETIC,
            severity=AlertSeverity.ATTENTION,
            headline=f"{item.description}: {item.qty:g} × "
                     f"{format_inr(item.rate)} comes to {format_inr(expected)}, "
                     f"not {format_inr(item.amount)}",
            detail=(
                f"{format_inr(abs(difference))} "
                f"{'more' if difference > 0 else 'less'} than the line multiplies out."
            ),
            ask="Ask which of the three figures is the right one. A quantity "
                "entered against the wrong rate is the commonest billing slip "
                "there is.",
            amount=round_inr(max(difference, ZERO)),
            lines=[item.line_no],
        ))
    return findings


def _totals(bill: ReadBill) -> list[BillFinding]:
    if bill.gross_total is None:
        return []
    difference = bill.line_total - bill.gross_total
    if abs(difference) <= PENNY:
        return []
    # Some bills print the figure after discount as the gross. Recognising that
    # avoids raising a mismatch that is only a naming convention.
    if bill.discount > 0 and abs(difference - bill.discount) <= PENNY:
        return []

    return [BillFinding(
        kind=FindingKind.TOTAL_MISMATCH,
        severity=AlertSeverity.URGENT,
        headline=f"The lines come to {format_inr(bill.line_total)}, the bill "
                 f"says {format_inr(bill.gross_total)}",
        detail=f"A difference of {format_inr(abs(difference))}.",
        ask="Ask for the total to be recalculated in front of you. Either a "
            "line is missing from the printout or the total is wrong, and both "
            "are worth settling before anybody signs.",
        amount=round_inr(abs(difference)),
        lines=[],
    )]


def _unplaced(bill: ReadBill) -> list[BillFinding]:
    unplaced = [i for i in bill.items if i.head is None]
    if not unplaced:
        return []
    total = round_inr(sum((i.amount for i in unplaced), ZERO))
    return [BillFinding(
        kind=FindingKind.UNPLACED,
        severity=AlertSeverity.INFO,
        headline=f"{len(unplaced)} line{'s' if len(unplaced) > 1 else ''} we "
                 f"could not place, {format_inr(total)}",
        detail=_names(unplaced) + ".",
        ask="These were left out of the settlement below rather than guessed "
            "at, so the figures there are lower than the whole bill by this "
            "much.",
        amount=total,
        lines=[i.line_no for i in unplaced],
    )]


# --- what the policy will do to it ------------------------------------------


def _room_facts(
    bill: ReadBill, room_category: RoomCategory | None, policy: NormalizedPolicy
) -> tuple[Decimal, float, float, RoomCategory]:
    """Rate per day, nights, ICU days and room tier, read off the bill itself."""
    room = next((i for i in bill.placed if i.head is ExpenseHead.ROOM_RENT), None)
    icu = next((i for i in bill.placed if i.head is ExpenseHead.ICU_CHARGES), None)

    nights = float(room.qty) if room and room.qty else (1.0 if room else 0.0)
    icu_days = float(icu.qty) if icu and icu.qty else (1.0 if icu else 0.0)

    rate = ZERO
    if room is not None:
        rate = room.rate if room.rate is not None else round_inr(
            room.amount / Decimal(str(nights or 1))
        )

    category = room_category
    if category is None and room is not None:
        named = parse_room_category(room.description)
        category = RoomCategory(named) if named else None
    if category is None:
        # Unknown is not a reason to invent a tier. The policy's own ceiling
        # leaves the category test neutral, so only the rupee cap decides, and
        # the rupee cap is what actually bites.
        category = policy.room_limit.category_ceiling or RoomCategory.SINGLE_PRIVATE

    return rate, nights + icu_days, icu_days, category


def _settle(
    bill: ReadBill,
    policy: NormalizedPolicy,
    *,
    hospital_name: str,
    hospital_id: str,
    procedure_code: str,
    room_category: RoomCategory | None,
    is_network: bool,
    patient_age: int | None,
) -> SimulationResult:
    rate, stay, icu_days, category = _room_facts(bill, room_category, policy)

    estimated = EstimatedBill(
        hospital_id=hospital_id or "billed",
        procedure_code=procedure_code,
        room_category=category,
        los_days=max(stay, 1.0),
        icu_days=icu_days,
        room_rate_per_day=rate,
        lines=[
            BillLine(head=item.head, amount=item.amount, note=item.description)
            for item in bill.placed
            if item.head is not None
        ],
    )
    return waterfall.simulate(
        policy, estimated,
        hospital_name=hospital_name, is_network=is_network,
        room_category=category, patient_age=patient_age,
    )


_FROM_STEP: dict[DeductionKind, tuple[FindingKind, AlertSeverity, str]] = {
    DeductionKind.ROOM_RENT_CAP: (
        FindingKind.ROOM_ABOVE_CAP, AlertSeverity.ATTENTION,
        "This is not on the bill and the billing desk will not raise it. Your "
        "insurer takes it off at settlement, so it is yours to find.",
    ),
    DeductionKind.PROPORTIONATE: (
        FindingKind.PROPORTIONATE, AlertSeverity.URGENT,
        "Check how this was worked out. Since the IRDAI circular of May 2024 it "
        "applies to room-linked charges only: room, nursing, doctor visits, "
        "surgeon and theatre. If medicines, tests, implants or ICU have been "
        "reduced by the same fraction, that is worth querying with your insurer.",
    ),
    DeductionKind.SUBLIMIT: (
        FindingKind.SUBLIMIT, AlertSeverity.ATTENTION,
        "Ask your insurer to confirm the cap and what it counts against. The "
        "balance above it is yours.",
    ),
}


def _from_settlement(
    settlement: SimulationResult, bill: ReadBill, policy: NormalizedPolicy
) -> list[BillFinding]:
    """The deductions the bill does not show, said in the bill's own terms."""
    findings: list[BillFinding] = []
    for step in settlement.steps:
        mapped = _FROM_STEP.get(step.kind)
        if mapped is None or step.deducted <= ZERO:
            continue
        kind, severity, ask = mapped
        findings.append(BillFinding(
            kind=kind, severity=severity,
            headline=f"{step.label}: {format_inr(step.deducted)}",
            detail=step.explanation,
            ask=ask,
            amount=round_inr(step.deducted),
            lines=_lines_for_heads(bill, step.affected_heads),
        ))

    consumables = bill.by_head().get(ExpenseHead.CONSUMABLES, ZERO)
    if consumables > ZERO and not policy.covers_consumables:
        findings.append(BillFinding(
            kind=FindingKind.CONSUMABLES,
            severity=AlertSeverity.INFO,
            headline=f"Consumables on this bill: {format_inr(consumables)}",
            detail="Indian policies exclude consumables unless a rider was "
                   "bought, so this part is yours whichever way the rest goes.",
            ask="Worth checking the line is really consumables rather than "
                "medicines, which your policy does pay for.",
            amount=round_inr(consumables),
            lines=_lines_for_heads(bill, [ExpenseHead.CONSUMABLES]),
        ))
    return findings


def _lines_for_heads(bill: ReadBill, heads: list[ExpenseHead]) -> list[int]:
    wanted = set(heads)
    return [i.line_no for i in bill.items if i.head in wanted]


def _names(items: list[BilledItem], limit: int = 3) -> str:
    shown = [i.description for i in items[:limit]]
    rest = len(items) - len(shown)
    if rest > 0:
        shown.append(f"{rest} other{'s' if rest > 1 else ''}")
    if len(shown) == 1:
        return shown[0]
    return f"{', '.join(shown[:-1])} and {shown[-1]}"
