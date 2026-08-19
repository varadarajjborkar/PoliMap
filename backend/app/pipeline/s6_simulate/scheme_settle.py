"""Settlement under a government scheme, which is a package purchase.

The indemnity waterfall in `waterfall.py` answers "how much of this bill will my
insurer allow". Under a public scheme that question does not arise. The scheme
buys the treatment at its own fixed rate from a hospital that has agreed to
accept it, and the hospital's own tariff stops being the thing being settled.

Three consequences drive everything below.

**Empanelment is binary.** A hospital either accepts the scheme or it does not.
There is no reimbursement route for the package schemes, so a non-empanelled
hospital means the family pays privately in full. Telling them instead to
arrange the money and claim it back later is the single most harmful thing this
system could say to a scheme beneficiary, and it is what the indemnity path did.

**The package is all-inclusive.** Consumables, implants, drugs, diagnostics and
food are inside the rate. The heads an indemnity policy strips out first are
precisely the heads a scheme covers, so running the non-payable step over a
scheme patient produces a warning that is not merely wrong but inverted.

**The entitlement is a ward, not a rupee cap.** There is no room rent limit to
exceed and therefore no proportionate deduction. A patient who insists on a
private room in an empanelled hospital steps outside the package for the room,
and that is stated as a choice rather than modelled as a deduction.
"""

from __future__ import annotations

from decimal import Decimal

from app.core.logging import get_logger
from app.schemas.hospital import Hospital
from app.schemas.money import ZERO, apply_pct, format_inr, round_inr
from app.schemas.phrasing import Phrase, phrase
from app.schemas.policy import NormalizedPolicy, RoomCategory
from app.schemas.procedure import Procedure
from app.schemas.scheme import SchemeRules
from app.schemas.simulation import (
    DeductionKind,
    EstimatedBill,
    SettlementMode,
    SimulationResult,
    WaterfallStep,
)

log = get_logger(__name__)


def package_price(
    rules: SchemeRules, procedure: Procedure, hospital: Hospital
) -> Decimal:
    """What the scheme pays the hospital for this treatment.

    Anchored on the CGHS non-NABH rate rather than the hospital's own price,
    which is the point of a package rate: the scheme pays the same for the same
    treatment wherever it is done. A NABH hospital earns a modest uplift, as
    the package schemes do allow, but nothing like the private differential.
    """
    base = procedure.base_rate_non_nabh * rules.package_rate_factor
    if hospital.quality.accreditation.is_nabh_tier:
        base *= Decimal("1.10")
    return round_inr(base)


def settle_under_scheme(
    policy: NormalizedPolicy,
    rules: SchemeRules,
    bill: EstimatedBill,
    procedure: Procedure,
    hospital: Hospital,
    *,
    room_category: RoomCategory | None = None,
) -> SimulationResult:
    """Cost a treatment under a public scheme rather than an indemnity policy."""
    room = room_category or bill.room_category
    empanelled = rules.scheme in hospital.empanelled_schemes

    steps: list[WaterfallStep] = []
    warnings: list[Phrase] = []
    notes: list[str] = []

    if not empanelled:
        return _not_empanelled(policy, rules, bill, hospital, room)

    scheme_rate = package_price(rules, procedure, hospital)

    # The scheme cannot pay past what the family has left for the year. This is
    # the one place a scheme behaves like a cover: the ceiling is shared, so an
    # earlier admission by a relative can have spent it already.
    available = _available_cover(policy, rules)
    paid_by_scheme = min(scheme_rate, available)

    # Above the general ward the room stops being scheme business. The patient
    # pays the hospital's own rate for the upgrade, and nothing else changes.
    upgrade = ZERO
    if not room.is_within(rules.room_entitlement):
        upgrade = _room_upgrade_cost(bill, hospital, rules)

    copay = apply_pct(paid_by_scheme, rules.copay_pct) if rules.copay_pct else ZERO
    out_of_pocket = round_inr(upgrade + copay)

    steps.append(WaterfallStep(
        kind=DeductionKind.SCHEME_PACKAGE_RATE,
        deducted=round_inr(max(bill.total - paid_by_scheme, ZERO)),
        payable_after=paid_by_scheme,
        explanation=(
            f"{rules.label} buys this treatment at a fixed {format_inr(scheme_rate)}. "
            f"The hospital cannot bill you the gap from its own "
            f"{format_inr(bill.total)}. Consumables, implants, medicines, "
            f"tests and food are all inside the package."
        ),
        values={
            "scheme": rules.label,
            "rate": format_inr(scheme_rate),
            "price": format_inr(bill.total),
        },
        detail={
            "package_rate": float(scheme_rate),
            "hospital_price": float(bill.total),
            "scheme": rules.scheme.value,
        },
    ))

    if paid_by_scheme < scheme_rate:
        warnings.append(phrase(
            "warn.scheme_cover_short",
            f"Only {format_inr(available)} of your {rules.label} cover is left "
            f"this year, against {format_inr(scheme_rate)} for this treatment. "
            f"The hospital will ask you for the gap.",
            remaining=format_inr(available), scheme=rules.label,
            rate=format_inr(scheme_rate),
        ))
        out_of_pocket = round_inr(out_of_pocket + (scheme_rate - paid_by_scheme))

    if upgrade > 0:
        warnings.append(phrase(
            "warn.scheme_upgrade",
            f"You chose a {room.label}; {rules.label} covers a "
            f"{rules.room_entitlement.label}. The upgrade is yours, about "
            f"{format_inr(upgrade)} for the stay. Nothing else is reduced.",
            chosen=room.label, scheme=rules.label,
            covered=rules.room_entitlement.label, amount=format_inr(upgrade),
        ))
    else:
        notes.append(phrase(
            "note.scheme_room_free",
            f"A {rules.room_entitlement.label} is included free.",
            room=rules.room_entitlement.label,
        ))

    if out_of_pocket == 0:
        notes.append(phrase(
            "note.scheme_nothing_to_pay",
            "Nothing to pay here, and nothing to claim back later.",
        ))
    if rules.note:
        notes.append(phrase(f"scheme.note.{rules.scheme.value}", rules.note))
    if rules.post_hospitalisation_days:
        after = str(rules.post_hospitalisation_days)
        if rules.pre_hospitalisation_days:
            before = str(rules.pre_hospitalisation_days)
            notes.append(phrase(
                "note.scheme_window_both",
                f"Treatment {after} days after discharge is included, and "
                f"{before} days before admission.",
                after=after, before=before,
            ))
        else:
            notes.append(phrase(
                "note.scheme_window_after",
                f"Treatment {after} days after discharge is included.",
                after=after,
            ))

    return SimulationResult(
        hospital_id=bill.hospital_id,
        hospital_name=hospital.name,
        procedure_code=bill.procedure_code,
        room_category=room,
        bill=bill,
        steps=steps,
        payable_by_insurer=paid_by_scheme,
        out_of_pocket=out_of_pocket,
        # Nothing is fronted under a scheme. That is the entire promise of it,
        # and it is what makes an empanelled hospital reachable for a family
        # who could not raise a lakh at a counter tonight.
        cash_to_arrange_upfront=out_of_pocket,
        settlement_mode=SettlementMode.SCHEME_PACKAGE,
        warnings=warnings,
        notes=notes,
    )


def _available_cover(policy: NormalizedPolicy, rules: SchemeRules) -> Decimal:
    """Scheme cover left this year, honouring anything already spent."""
    if policy.sum_insured_remaining is not None:
        return policy.sum_insured_remaining
    if policy.sum_insured > 0:
        return policy.sum_insured
    return rules.cover_per_year


def _room_upgrade_cost(
    bill: EstimatedBill, hospital: Hospital, rules: SchemeRules
) -> Decimal:
    """What a room above the ward entitlement costs the patient outright."""
    chosen = hospital.tariff_for(bill.room_category)
    included = hospital.tariff_for(rules.room_entitlement)
    if chosen is None:
        return ZERO

    nights = Decimal(str(max(bill.los_days - bill.icu_days, 0.0)))
    included_rate = included.per_day if included else ZERO
    return round_inr(max(chosen.per_day - included_rate, ZERO) * nights)


def _not_empanelled(
    policy: NormalizedPolicy,
    rules: SchemeRules,
    bill: EstimatedBill,
    hospital: Hospital,
    room: RoomCategory,
) -> SimulationResult:
    """The scheme pays nothing here, and there is no claiming it back.

    Stated as its own outcome rather than folded into the ordinary path,
    because the advice that follows from it is the opposite of the advice for a
    non-network private insurer. There the family fronts the money and recovers
    it; here there is nothing to recover, and the honest thing to say is to go
    somewhere empanelled.
    """
    reimbursable = rules.reimbursement_possible

    return SimulationResult(
        hospital_id=bill.hospital_id,
        hospital_name=hospital.name,
        procedure_code=bill.procedure_code,
        room_category=room,
        bill=bill,
        steps=[WaterfallStep(
            kind=DeductionKind.SCHEME_NOT_EMPANELLED,
            deducted=bill.total,
            payable_after=ZERO,
            explanation=(
                f"{hospital.name} is not empanelled for {rules.label}, so the "
                f"scheme pays nothing here."
            ),
            values={"hospital": hospital.name, "scheme": rules.label},
            detail={"scheme": rules.scheme.value},
        )],
        payable_by_insurer=ZERO,
        out_of_pocket=bill.total,
        cash_to_arrange_upfront=bill.total,
        settlement_mode=SettlementMode.SCHEME_PACKAGE,
        warnings=[
            phrase(
                "warn.scheme_unusable_reimbursable",
                f"{rules.label} cannot be used here. Some costs may be claimed "
                f"back, but only with approval beforehand. Check before you "
                f"are admitted.",
                scheme=rules.label,
            )
            if reimbursable else
            phrase(
                "warn.scheme_unusable",
                f"{rules.label} cannot be used here, and there is nothing to "
                f"claim back later: it pays empanelled hospitals only. The "
                f"whole {format_inr(bill.total)} would be yours. Pick a "
                f"hospital that accepts {rules.label}.",
                scheme=rules.label, total=format_inr(bill.total),
            )
        ],
        notes=[],
    )
