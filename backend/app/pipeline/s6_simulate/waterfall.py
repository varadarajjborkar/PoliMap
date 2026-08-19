"""Stage 6: apply a policy to a bill and explain every rupee of the difference.

This is the question the problem statement says goes unanswered: not "am I
covered" but "what will I actually pay". The answer is produced as an ordered
chain of deductions, each naming the clause that caused it and stating its
effect in plain words, so a user can read down the chain and see where their
money went.

Order is not arbitrary. Insurers apply these tests in a specific sequence and
the sequence changes the answer: a co-payment taken before a sum-insured cap
gives a different result from one taken after. The order below follows Indian
settlement practice: remove what is never payable, apply the caps that bind
particular expenses, then the proportionate reduction, then the policyholder's
own share, and only then test the total against remaining cover.

The proportionate deduction is the part most people have never heard of and the
part that costs them most. Taking a room above your eligible category does not
just cost the difference in room rent; it reduces the payout on everything
priced by room tier: surgeon, theatre and nursing. Since the IRDAI master circular
of May 2024 it no longer touches ICU, pharmacy, diagnostics, implants or
consumables, and modelling that boundary correctly is the difference between a
useful estimate and a scary wrong one.
"""

from __future__ import annotations

from decimal import Decimal

from app.core.logging import get_logger
from app.schemas.money import ZERO, apply_pct, apply_ratio, format_inr, round_inr
from app.schemas.phrasing import Phrase, phrase
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    is_never_payable,
    is_room_linked,
)
from app.schemas.simulation import (
    CostBand,
    DeductionKind,
    EstimatedBill,
    SettlementMode,
    SimulationResult,
    WaterfallStep,
)

log = get_logger(__name__)


def _format_ratio(ratio: Decimal) -> str:
    """Percentage with a decimal only when rounding would distort it.

    The canonical case is 5,000 against 8,000, which is exactly 62.5%. Printing
    "62%" beside a figure derived from 62.5% invites a user to conclude the
    arithmetic is wrong.
    """
    pct = ratio * 100
    rounded = pct.quantize(Decimal("0.1"))
    if rounded == rounded.to_integral_value():
        return f"{int(rounded)}%"
    return f"{rounded.normalize()}%"


class _Ledger:
    """Per-head running balances as deductions are applied.

    Deductions are tracked head by head rather than as one running total,
    because proportionate deduction applies to some heads and not others, and a
    single total cannot express that.
    """

    def __init__(self, bill: EstimatedBill) -> None:
        self.amounts: dict[ExpenseHead, Decimal] = bill.by_head()
        self.original: dict[ExpenseHead, Decimal] = dict(self.amounts)

    @property
    def total(self) -> Decimal:
        return round_inr(sum(self.amounts.values(), ZERO))

    def reduce(self, head: ExpenseHead, by: Decimal) -> Decimal:
        """Take `by` off a head, never below zero. Returns what was taken."""
        available = self.amounts.get(head, ZERO)
        taken = min(available, max(by, ZERO))
        self.amounts[head] = available - taken
        return taken

    def zero(self, head: ExpenseHead) -> Decimal:
        return self.reduce(head, self.amounts.get(head, ZERO))


def simulate(
    policy: NormalizedPolicy,
    bill: EstimatedBill,
    *,
    hospital_name: str = "",
    is_network: bool = True,
    room_category: RoomCategory | None = None,
    patient_age: int | None = None,
) -> SimulationResult:
    """Adjudicate a bill against a policy, recording every deduction."""
    room = room_category or bill.room_category
    ledger = _Ledger(bill)
    steps: list[WaterfallStep] = []
    warnings: list[Phrase] = []
    notes: list[Phrase] = []

    # Each step's deduction is measured from the ledger rather than supplied by
    # the caller. Percentages are rounded per expense head, so a requested
    # figure and the amount actually removable differ by a rupee or two, and a
    # waterfall that reports the request drifts out of balance with its own
    # totals. Measuring the delta makes reconciliation structural: the steps
    # cannot fail to sum to the difference, because that difference is what
    # they are.
    running = [ledger.total]

    def record(
        kind: DeductionKind,
        explanation: str,
        *,
        key: str = "",
        values: dict[str, str] | None = None,
        heads: list[ExpenseHead] | None = None,
        clause_ids: list[str] | None = None,
        **detail: float | str,
    ) -> None:
        after = ledger.total
        deducted = running[0] - after
        running[0] = after
        if deducted <= 0:
            return
        steps.append(WaterfallStep(
            kind=kind,
            deducted=deducted,
            payable_after=after,
            explanation=explanation,
            key=key,
            values=values or {},
            affected_heads=heads or [],
            clause_ids=clause_ids or [],
            detail=detail,
        ))

    # 1. Items no health policy reimburses, unless a consumables rider was bought.
    non_payable = ZERO
    removed_heads: list[ExpenseHead] = []
    for head in list(ledger.amounts):
        if is_never_payable(head):
            non_payable += ledger.zero(head)
            removed_heads.append(head)

    if not policy.covers_consumables:
        non_payable += ledger.zero(ExpenseHead.CONSUMABLES)
        removed_heads.append(ExpenseHead.CONSUMABLES)
    else:
        notes.append(phrase(
            "note.consumables_covered",
            "Your policy does cover consumables.",
        ))

    if policy.covers_consumables:
        record(
            DeductionKind.NON_PAYABLE,
            "Gloves, syringes and registration are never covered.",
            key="non_payable",
            heads=removed_heads,
        )
    else:
        record(
            DeductionKind.NON_PAYABLE,
            "Gloves, syringes and registration are never covered, and "
            "consumables need an add-on you do not have.",
            key="non_payable_consumables",
            heads=removed_heads,
        )

    # 2. Per-head caps.
    for sublimit in policy.sublimits:
        if sublimit.head is None:
            continue
        current = ledger.amounts.get(sublimit.head, ZERO)
        cap = sublimit.resolve(policy.sum_insured, days=max(int(bill.los_days), 1))
        if current > cap:
            ledger.reduce(sublimit.head, current - cap)
            record(
                DeductionKind.SUBLIMIT,
                f"{sublimit.head.label} is capped at {format_inr(cap)}. "
                f"The estimate is {format_inr(current)}.",
                values={
                    "head": sublimit.head.label,
                    "cap": format_inr(cap),
                    "billed": format_inr(current),
                },
                heads=[sublimit.head],
                clause_ids=sublimit.source_clause_ids,
                cap=float(cap), billed=float(current),
            )

    # 3. Room rent cap, then the proportionate reduction it triggers.
    room_cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    eligible_ceiling = policy.room_limit.category_ceiling
    ratio = Decimal(1)

    if room_cap is not None and bill.room_rate_per_day > room_cap and bill.los_days > 0:
        nights = Decimal(str(bill.los_days)) - Decimal(str(bill.icu_days))
        nights = max(nights, ZERO)
        excess = (bill.room_rate_per_day - room_cap) * nights
        # The return value is deliberately unused: `record` measures each step
        # from the ledger's own delta, so the waterfall cannot fail to sum.
        ledger.reduce(ExpenseHead.ROOM_RENT, excess)
        record(
            DeductionKind.ROOM_RENT_CAP,
            f"Your room is {format_inr(bill.room_rate_per_day)} a day and you "
            f"are covered for {format_inr(room_cap)}. You pay the gap.",
            values={
                "rate": format_inr(bill.room_rate_per_day),
                "cap": format_inr(room_cap),
            },
            heads=[ExpenseHead.ROOM_RENT],
            clause_ids=policy.room_limit.source_clause_ids,
            eligible_per_day=float(room_cap),
            actual_per_day=float(bill.room_rate_per_day),
        )

        ratio = room_cap / bill.room_rate_per_day
        linked_total = ZERO
        linked_heads: list[ExpenseHead] = []
        for head, amount in list(ledger.amounts.items()):
            if head is ExpenseHead.ROOM_RENT or amount <= 0:
                continue
            if not is_room_linked(head, policy.deduction_regime):
                continue
            reduction = amount - apply_ratio(amount, ratio)
            linked_total += ledger.reduce(head, reduction)
            linked_heads.append(head)

        record(
            DeductionKind.PROPORTIONATE,
            f"Your room is above your category, so only {_format_ratio(ratio)} "
            f"is paid on charges priced by room: surgeon, theatre and nursing. "
            f"ICU, medicines, tests and implants are untouched.",
            values={"pct": _format_ratio(ratio)},
            heads=linked_heads,
            clause_ids=policy.room_limit.source_clause_ids,
            ratio=float(round(ratio, 4)),
        )
        if linked_total > 0:
            warnings.append(phrase(
                "warn.proportionate",
                f"This room also costs about {format_inr(linked_total)} in "
                f"proportionate cuts, on top of the room gap.",
                amount=format_inr(linked_total),
            ))

    elif eligible_ceiling is not None and not room.is_within(eligible_ceiling):
        # A category entitlement with no rupee figure attached. The reduction
        # cannot be computed, but staying silent would be worse than saying so.
        warnings.append(phrase(
            "warn.room_category",
            f"You are covered for a {eligible_ceiling.label} and have chosen a "
            f"{room.label}. Related charges are likely to be cut. Ask the "
            f"insurance desk.",
            covered=eligible_ceiling.label, chosen=room.label,
        ))

    # 4. A cap on this specific treatment.
    procedure_cap = policy.sublimit_for_procedure(bill.procedure_code)
    if procedure_cap is not None:
        cap = procedure_cap.resolve(policy.sum_insured)
        if ledger.total > cap:
            _reduce_proportionally(ledger, ledger.total - cap)
            record(
                DeductionKind.PROCEDURE_CAP,
                f"Your policy caps this treatment at {format_inr(cap)}.",
                values={"cap": format_inr(cap)},
                clause_ids=procedure_cap.source_clause_ids,
                cap=float(cap),
            )

    # 5. The policyholder's own share, taken on what remains admissible.
    #
    # Most policies carrying a co-payment band it on age, and the band is the
    # whole point: applied to everyone it takes a fifth off a child's claim on
    # a policy written so that it does not.
    copay = policy.copay_for(patient_age)
    if copay > 0:
        _reduce_proportionally(ledger, apply_pct(ledger.total, copay))
        if policy.copay_above_age:
            record(
                DeductionKind.COPAY,
                f"You pay {copay:g}% of every approved claim, the co-payment "
                f"for ages {policy.copay_above_age} and above.",
                key="copay_age",
                values={"pct": f"{copay:g}", "age": str(policy.copay_above_age)},
                pct=float(copay),
            )
        else:
            record(
                DeductionKind.COPAY,
                f"You pay {copay:g}% of every approved claim.",
                key="copay",
                values={"pct": f"{copay:g}"},
                pct=float(copay),
            )
    elif policy.copay_pct > 0 and policy.copay_above_age:
        notes.append(phrase(
            "note.copay_not_applicable",
            f"The {policy.copay_pct:g}% co-payment starts at age "
            f"{policy.copay_above_age}, so it does not apply here.",
            pct=f"{policy.copay_pct:g}", age=str(policy.copay_above_age),
        ))

    # 6. Deductible: the band a top-up plan only starts paying above.
    if policy.deductible > 0:
        _reduce_proportionally(ledger, min(policy.deductible, ledger.total))
        record(
            DeductionKind.DEDUCTIBLE,
            f"A top-up policy. It pays only above "
            f"{format_inr(policy.deductible)}, which is yours to cover or "
            f"another policy's.",
            values={"amount": format_inr(policy.deductible)},
            deductible=float(policy.deductible),
        )

    # 7. Finally, what is left cannot exceed the cover remaining.
    available = policy.available_cover
    if ledger.total > available:
        _reduce_proportionally(ledger, ledger.total - available)
        record(
            DeductionKind.SUM_INSURED_EXHAUSTED,
            f"Only {format_inr(available)} of cover is left this year, and the "
            f"claim is above it.",
            values={"remaining": format_inr(available)},
            remaining_cover=float(available),
        )
        warnings.append(phrase(
            "warn.cover_used_up",
            f"This treatment would use up the {format_inr(available)} you have "
            f"left.",
            remaining=format_inr(available),
        ))
        if policy.restore_benefit:
            # Deliberately a note rather than money added to this estimate.
            # Restoration reinstates the cover, but whether it can be drawn on
            # by the admission that exhausted it or only by a later one differs
            # between products, and inventing the favourable reading here would
            # understate what somebody has to arrange before they are admitted.
            notes.append(phrase(
                "note.restore",
                f"This policy restores cover once a year, putting "
                f"{format_inr(policy.sum_insured)} back for a later admission. "
                f"Ask your insurer if it can be used for this one; policies "
                f"differ.",
                amount=format_inr(policy.sum_insured),
            ))

    payable = ledger.total
    out_of_pocket = round_inr(bill.total - payable)

    # What is left on the patient, head by head. A second policy settling the
    # balance adjudicates it against its own room cap and sub-limits, and one
    # combined figure cannot be adjudicated.
    unpaid = {
        head: round_inr(original - ledger.amounts.get(head, ZERO))
        for head, original in ledger.original.items()
        if original - ledger.amounts.get(head, ZERO) > 0
    }

    if policy.government_scheme:
        mode = SettlementMode.SCHEME_PACKAGE
    elif is_network and policy.cashless_available:
        mode = SettlementMode.CASHLESS
    else:
        mode = SettlementMode.REIMBURSEMENT

    # Under reimbursement the family funds the entire bill first and waits.
    # That is a different problem from the final cost and is reported separately.
    cash_upfront = bill.total if mode is SettlementMode.REIMBURSEMENT else out_of_pocket
    if mode is SettlementMode.REIMBURSEMENT:
        warnings.append(phrase(
            "warn.not_cashless",
            f"Not a cashless hospital for you. You would pay the full "
            f"{format_inr(bill.total)} here and claim {format_inr(payable)} "
            f"back later.",
            total=format_inr(bill.total), payable=format_inr(payable),
        ))

    return SimulationResult(
        hospital_id=bill.hospital_id,
        hospital_name=hospital_name,
        procedure_code=bill.procedure_code,
        room_category=room,
        bill=bill,
        steps=steps,
        payable_by_insurer=payable,
        out_of_pocket=out_of_pocket,
        unpaid=unpaid,
        cash_to_arrange_upfront=cash_upfront,
        settlement_mode=mode,
        warnings=warnings,
        notes=notes,
    )


def _reduce_proportionally(ledger: _Ledger, amount: Decimal) -> Decimal:
    """Spread a whole-bill deduction across the heads still carrying value.

    Co-payments and cover limits apply to the claim as a whole, not to any one
    expense. Spreading them keeps the per-head balances meaningful for anything
    applied afterwards.

    Returns what was *actually* removed, which can differ from what was asked
    for by a rupee or two: each head is rounded independently and the residue
    has to land somewhere. Callers record the returned figure rather than their
    request, so the waterfall always reconciles against the balances it
    produced instead of drifting by the rounding error.
    """
    total = ledger.total
    if total <= 0 or amount <= 0:
        return ZERO

    target = min(round_inr(amount), total)
    ratio = target / total
    taken = ZERO

    # Largest heads first, so the residue pass has somewhere to land.
    order = sorted(ledger.amounts, key=lambda h: ledger.amounts[h], reverse=True)
    for head in order:
        if ledger.amounts[head] <= 0:
            continue
        taken += ledger.reduce(head, apply_ratio(ledger.amounts[head], ratio))

    residue = target - taken
    for head in order:
        if residue <= 0:
            break
        if ledger.amounts[head] <= 0:
            continue
        residue -= ledger.reduce(head, residue)

    return target - max(residue, ZERO)


def with_band(
    result: SimulationResult, low: SimulationResult, high: SimulationResult
) -> SimulationResult:
    """Attach a low/expected/high range built from shorter and longer stays."""
    result.band = CostBand(
        low=min(low.out_of_pocket, result.out_of_pocket),
        expected=result.out_of_pocket,
        high=max(high.out_of_pocket, result.out_of_pocket),
    )
    return result
