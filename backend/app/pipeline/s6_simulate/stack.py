"""Two policies on one admission.

A great many Indian families hold more than one: an employer's group cover and
a personal policy, or a modest base policy with a top-up sitting above it. Only
one of them is ever consulted, because every tool that reads a policy reads one
policy, and the second sits in a drawer while the family pays a bill it would
have covered.

Under IRDAI's rules the policyholder chooses which insurer to approach first,
and the second settles the balance against its own terms. That is what happens
here: the first policy adjudicates the bill, what the patient is left with
becomes the bill put to the second, and the second applies its own room cap,
its own sub-limits and its own co-payment to that.

Which order is better is not asserted. Both are run and the cheaper is reported,
with the difference stated, because the ordering rule people are usually given
("claim from the corporate policy first") is a rule of thumb that a top-up or an
exhausted sum insured can turn upside down. Being told which way round is worth
more than being told a rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.pipeline.s6_simulate.waterfall import simulate
from app.schemas.money import ZERO, format_inr, round_inr
from app.schemas.phrasing import Phrase, phrase
from app.schemas.policy import NormalizedPolicy
from app.schemas.simulation import (
    BillLine,
    EstimatedBill,
    RoomCategory,
    SettlementMode,
    SimulationResult,
)


@dataclass
class Leg:
    """One policy's part in settling one bill."""

    policy_id: str
    label: str
    result: SimulationResult

    @property
    def pays(self) -> Decimal:
        return self.result.payable_by_insurer


@dataclass
class StackedResult:
    """What two policies together leave the patient paying."""

    legs: list[Leg]
    bill_total: Decimal
    payable: Decimal
    out_of_pocket: Decimal
    cash_to_arrange_upfront: Decimal
    order_note: Phrase
    """Which policy was put first, and what the other order would have cost."""
    alternative_out_of_pocket: Decimal | None = None
    warnings: list[Phrase] = None  # type: ignore[assignment]
    notes: list[Phrase] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.notes is None:
            self.notes = []

    @property
    def primary(self) -> SimulationResult:
        """The leading policy's own result, which carries the bill and steps."""
        return self.legs[0].result


def label_for(policy: NormalizedPolicy) -> str:
    """How to name a policy back to somebody holding two of them."""
    parts = [policy.meta.insurer_name, policy.meta.plan_name]
    name = " ".join(p for p in parts if p).strip()
    if not name:
        name = policy.meta.policy_type or "Your other policy"
    if policy.deductible > 0:
        name = f"{name} (top-up)"
    return name


def residual_bill(bill: EstimatedBill, result: SimulationResult) -> EstimatedBill:
    """The part of the bill the first policy left, as a bill in its own right.

    The room rate and the length of stay carry over unchanged, because the
    second policy applies its own cap to the room actually occupied, not to
    whatever fraction of the room rent is still outstanding.
    """
    by_label = {line.head: line.label for line in bill.lines}
    lines = [
        BillLine(head=head, label=by_label.get(head, head.label), amount=amount)
        for head, amount in result.unpaid.items()
        if amount > 0
    ]
    return EstimatedBill(
        hospital_id=bill.hospital_id,
        procedure_code=bill.procedure_code,
        room_category=bill.room_category,
        los_days=bill.los_days,
        icu_days=bill.icu_days,
        room_rate_per_day=bill.room_rate_per_day,
        lines=lines,
    )


def is_top_up(policy: NormalizedPolicy) -> bool:
    """Whether this policy only starts paying above a band somebody else covers."""
    return policy.deductible > 0


def _with_deductible_met(
    policy: NormalizedPolicy, already_paid: Decimal
) -> NormalizedPolicy:
    """The same policy with its deductible reduced by what has already been paid.

    A top-up's deductible is a band on the whole bill, not on the fraction of
    it that reaches this insurer. Once an earlier policy has paid through that
    band, the band is met, and applying it a second time to the residual would
    take the same money off twice: it is the difference between a super top-up
    paying the entire balance and paying nothing at all.
    """
    if policy.deductible <= 0 or already_paid <= 0:
        return policy
    adjusted = policy.model_copy(deep=True)
    adjusted.deductible = max(ZERO, policy.deductible - already_paid)
    return adjusted


def _run_in_order(
    policies: list[NormalizedPolicy],
    bill: EstimatedBill,
    *,
    hospital_name: str,
    is_network: bool,
    room_category: RoomCategory | None,
    patient_age: int | None,
) -> list[Leg]:
    legs: list[Leg] = []
    remaining = bill
    paid_so_far = ZERO

    for policy in policies:
        if remaining.total <= 0:
            break
        result = simulate(
            _with_deductible_met(policy, paid_so_far), remaining,
            hospital_name=hospital_name, is_network=is_network,
            room_category=room_category, patient_age=patient_age,
        )
        legs.append(Leg(policy.policy_id, label_for(policy), result))
        paid_so_far += result.payable_by_insurer
        remaining = residual_bill(remaining, result)

    return legs


def _left_paying(legs: list[Leg]) -> Decimal:
    return legs[-1].result.out_of_pocket if legs else ZERO


def settle_across(
    policies: list[NormalizedPolicy],
    bill: EstimatedBill,
    *,
    hospital_name: str = "",
    is_network: bool = True,
    room_category: RoomCategory | None = None,
    patient_age: int | None = None,
) -> StackedResult:
    """Adjudicate one bill against two policies, in whichever order costs less."""
    if len(policies) < 2:
        raise ValueError("settle_across needs two policies")

    def run(order: list[NormalizedPolicy]) -> list[Leg]:
        return _run_in_order(
            order, bill, hospital_name=hospital_name, is_network=is_network,
            room_category=room_category, patient_age=patient_age,
        )

    # One order is not a choice. A top-up pays only above a band that somebody
    # else has to cover first, so putting it in front is not an option an
    # insurer will entertain, however well the arithmetic comes out. Where a
    # rule settles it, the rule settles it; where nothing does, both orders are
    # run and the cheaper reported, because the advice people are usually given
    # is a rule of thumb that an exhausted sum insured turns upside down.
    tops = [p for p in policies if is_top_up(p)]
    if tops and len(tops) < len(policies):
        best = run([p for p in policies if not is_top_up(p)] + tops)
        other = None
    else:
        forward = run(list(policies))
        backward = run(list(reversed(policies)))
        best, other = (
            (forward, backward)
            if _left_paying(forward) <= _left_paying(backward)
            else (backward, forward)
        )

    payable = round_inr(sum((leg.pays for leg in best), ZERO))
    out_of_pocket = _left_paying(best)
    alternative = _left_paying(other) if other is not None else None

    lead = best[0].label
    second = best[-1].label if len(best) > 1 else ""
    if other is None:
        order_note = phrase(
            "order.forced",
            f"Claim from {lead} first, then {second} for the rest. It has to be "
            f"that way round: a top-up pays only above a band the other policy "
            f"covers first.",
            lead=lead, second=second,
        )
    elif alternative is not None and alternative > out_of_pocket:
        order_note = phrase(
            "order.cheaper",
            f"Claim from {lead} first, then {second} for the rest. The other "
            f"way round would leave you paying {format_inr(alternative)} "
            f"instead of {format_inr(out_of_pocket)}.",
            lead=lead, second=second,
            other=format_inr(alternative), this=format_inr(out_of_pocket),
        )
    else:
        order_note = phrase(
            "order.same",
            f"Claim from {lead} first, then {second} for the rest. Either order "
            f"comes to the same figure here.",
            lead=lead, second=second,
        )

    # Upfront cash is not the sum of the legs. Under reimbursement a family
    # funds the whole bill and waits, whichever policy eventually pays, and
    # that is the number deciding whether they can use the hospital at all.
    upfront = (
        bill.total
        if any(
            leg.result.settlement_mode is SettlementMode.REIMBURSEMENT
            for leg in best
        )
        else out_of_pocket
    )

    warnings = [w for leg in best for w in leg.result.warnings]
    notes = [n for leg in best for n in leg.result.notes]
    notes.append(phrase(
        "note.which_insurer_first",
        "Under IRDAI rules you choose which insurer to approach first. Tell "
        "each about the other: a claim settled without disclosing the second "
        "policy can be reopened.",
    ))

    return StackedResult(
        legs=best,
        bill_total=bill.total,
        payable=payable,
        out_of_pocket=out_of_pocket,
        cash_to_arrange_upfront=upfront,
        order_note=order_note,
        alternative_out_of_pocket=(
            alternative if alternative is not None and alternative != out_of_pocket
            else None
        ),
        warnings=warnings,
        notes=notes,
    )
