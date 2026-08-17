"""What the charges recorded so far actually mean, adjudicated.

The tracker used to sum recorded charges and show the total. That total is the
hospital's number, not the family's: it says what has been billed, and says
nothing about what the insurer will allow, which is the only figure anyone
cares about. Worse, the estimator on the previous screen had already computed
the second figure properly, so the two screens disagreed in public and a reader
had no way to know which to trust.

Everything recorded now goes through the same waterfall that produced the
estimate. That is the point: one engine, so the number at the top of the stay
screen is the same kind of number as the one that recommended the hospital.

The room is the case that made this urgent. A room rate typed at a billing
counter used to go in as an ordinary charge and was never compared to the
policy's cap, while the proportionate-deduction warning tested a rate captured
once at admission from the hospital's tariff. So a family could enter nine
thousand a day against a five thousand limit and be told nothing at all, by a
system whose previous screen had explained that exact rule to them.
"""

from __future__ import annotations

from decimal import Decimal

from app.pipeline.s6_simulate.waterfall import simulate
from app.schemas.journey import JourneyState
from app.schemas.money import ZERO, round_inr
from app.schemas.policy import ExpenseHead, NormalizedPolicy, RoomCategory
from app.schemas.scheme import rules_for
from app.schemas.simulation import (
    BillLine,
    EstimatedBill,
    SettlementMode,
    SimulationResult,
)


def observed_room_rate(state: JourneyState) -> Decimal | None:
    """The daily room rate the recorded charges actually imply.

    Taken from what the user typed rather than from the tariff captured at
    admission, because those disagree exactly when it matters: a patient moved
    to a different room, or a hospital billing a rate other than its published
    one. Where no room charge has been recorded, the booked rate stands.
    """
    room_charges = [c for c in state.costs if c.head is ExpenseHead.ROOM_RENT]
    if not room_charges:
        return state.room_rate_per_day

    total = sum((c.amount for c in room_charges), ZERO)
    # Each entry is read as one day's room rent. That is how the charge is
    # billed and how a user enters it, and assuming otherwise would silently
    # halve a rate that is about to be tested against a cap.
    days = Decimal(len(room_charges))
    return round_inr(total / days)


def bill_so_far(state: JourneyState, policy: NormalizedPolicy) -> EstimatedBill:
    """The charges recorded so far, shaped as a bill the waterfall can read."""
    by_head = state.accrued_by_head()
    rate = observed_room_rate(state) or ZERO

    return EstimatedBill(
        hospital_id=state.hospital_id or "",
        procedure_code=state.procedure_code or "",
        room_category=state.room_category or RoomCategory.GENERAL_WARD,
        los_days=float(max(state.days_elapsed, 1)),
        icu_days=0.0,
        room_rate_per_day=rate,
        lines=[
            BillLine(head=head, amount=amount)
            for head, amount in by_head.items()
            if amount > 0
        ],
    )


def position(
    state: JourneyState, policy: NormalizedPolicy, *, is_network: bool = True
) -> SimulationResult | None:
    """Adjudicate everything billed so far. None when nothing is recorded yet.

    A scheme beneficiary is deliberately not run through this. Under a package
    rate the hospital cannot bill the family for the items making up the
    package, so summing those items and deducting from them would invent an
    exposure that does not exist.
    """
    if not state.costs:
        return None
    if rules_for(policy.government_scheme) is not None:
        return None

    bill = bill_so_far(state, policy)
    if bill.total <= 0:
        return None

    return simulate(
        policy, bill,
        hospital_name=state.hospital_name,
        is_network=is_network,
        room_category=bill.room_category,
    )


def room_rate_conflict(
    state: JourneyState,
) -> tuple[Decimal, Decimal] | None:
    """A recorded room rate that disagrees with the one booked at admission.

    Returned as a pair rather than resolved silently. Somebody typing nine
    thousand a day into a stay booked at fourteen hundred has either changed
    room, mistyped, or been billed something they should query, and all three
    are worth one sentence on screen rather than a guess.
    """
    booked = state.room_rate_per_day
    observed = observed_room_rate(state)
    if booked is None or observed is None or booked <= 0:
        return None

    # A tenth either way is billing noise, not a discrepancy worth raising.
    if abs(observed - booked) <= booked / Decimal(10):
        return None
    return booked, observed


def settlement_mode(
    policy: NormalizedPolicy, *, is_network: bool = True
) -> SettlementMode:
    if rules_for(policy.government_scheme) is not None:
        return SettlementMode.SCHEME_PACKAGE
    if is_network and policy.cashless_available:
        return SettlementMode.CASHLESS
    return SettlementMode.REIMBURSEMENT
