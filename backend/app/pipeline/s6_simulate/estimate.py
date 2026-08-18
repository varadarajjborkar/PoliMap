"""One way in to costing a treatment, so nothing downstream can disagree.

Two things used to answer "what will this cost": the matcher costed options
through the indemnity waterfall, and the journey tracker summed recorded charges
without adjudicating them at all. They contradicted each other on the same
screen, which is worse than either being wrong alone, because a reader has no
way to tell which of the two to believe.

Everything that needs a number now comes through here. That also puts the choice
between a commercial policy and a public scheme in exactly one place: a scheme
does not settle against a bill, and dispatching on it anywhere else means some
caller eventually forgets and tells a PM-JAY family to arrange a lakh in cash.
"""

from __future__ import annotations

from app.pipeline.s6_simulate.bill import adverse_bill, estimate_bill, stay_range
from app.pipeline.s6_simulate.scheme_settle import settle_under_scheme
from app.pipeline.s6_simulate.stack import settle_across
from app.pipeline.s6_simulate.waterfall import simulate
from app.schemas.hospital import Hospital
from app.schemas.money import format_inr
from app.schemas.policy import NormalizedPolicy, RoomCategory
from app.schemas.procedure import Procedure
from app.schemas.scheme import rules_for
from app.schemas.simulation import (
    CostBand,
    DeductionKind,
    SimulationResult,
    WaterfallStep,
)


def estimate_across(
    policies: list[NormalizedPolicy],
    hospital: Hospital,
    procedure: Procedure,
    room: RoomCategory,
    *,
    is_network: bool = True,
    patient_age: int | None = None,
) -> SimulationResult:
    """Cost one treatment against two policies settling in sequence.

    Returned as a single `SimulationResult` so everything downstream, ranking,
    the journey, the interface, keeps working on one shape. The leading
    policy's own waterfall is what the result carries, since that is the
    adjudication somebody actually watches happen at the counter; the second
    policy's contribution arrives as one further step, and the totals are the
    stack's.
    """
    bill = estimate_bill(hospital, procedure, room)
    settled = settle_across(
        policies, bill, hospital_name=hospital.name,
        is_network=is_network, patient_age=patient_age,
    )

    result = settled.legs[0].result
    for leg in settled.legs[1:]:
        if leg.pays <= 0:
            continue
        result.steps.append(WaterfallStep(
            kind=DeductionKind.SECOND_POLICY,
            label=f"{leg.label} settles the balance",
            deducted=-leg.pays,
            payable_after=settled.payable,
            explanation=(
                f"{leg.label} pays {format_inr(leg.pays)} of what "
                f"{settled.legs[0].label} left."
            ),
        ))

    result.payable_by_insurer = settled.payable
    result.out_of_pocket = settled.out_of_pocket
    result.cash_to_arrange_upfront = settled.cash_to_arrange_upfront
    result.warnings = settled.warnings
    result.notes = [settled.order_note, *settled.notes]
    return result


def estimate_for(
    policy: NormalizedPolicy,
    hospital: Hospital,
    procedure: Procedure,
    room: RoomCategory,
    *,
    is_network: bool = True,
    with_band: bool = True,
    patient_age: int | None = None,
) -> SimulationResult:
    """Cost one treatment at one hospital, under whichever model applies."""
    rules = rules_for(policy.government_scheme)
    bill = estimate_bill(hospital, procedure, room)

    if rules is not None:
        result = settle_under_scheme(
            policy, rules, bill, procedure, hospital, room_category=room
        )
        if with_band:
            result.band = _scheme_band(policy, rules, procedure, hospital, room)
        return result

    result = simulate(
        policy, bill, hospital_name=hospital.name,
        is_network=is_network, room_category=room, patient_age=patient_age,
    )
    if with_band:
        result.band = _indemnity_band(
            policy, hospital, procedure, room,
            is_network=is_network, expected=result,
        )
    return result


def _indemnity_band(
    policy: NormalizedPolicy,
    hospital: Hospital,
    procedure: Procedure,
    room: RoomCategory,
    *,
    is_network: bool,
    expected: SimulationResult,
) -> CostBand:
    """A short stay against a complicated one, both adjudicated in full.

    The high side is a different bill, not the same bill scaled. Running it
    through the waterfall is what makes the figure defensible: a second implant
    is not merely more money, it can cross a sub-limit, and only adjudicating it
    shows that.
    """
    short_stay, _ = stay_range(procedure)
    low = simulate(
        policy,
        estimate_bill(hospital, procedure, room, los_days=short_stay, icu_days=0.0),
        hospital_name=hospital.name, is_network=is_network, room_category=room,
    )

    bad_bill, driver = adverse_bill(hospital, procedure, room)
    high = simulate(
        policy, bad_bill, hospital_name=hospital.name,
        is_network=is_network, room_category=room,
    )

    return CostBand(
        low=min(low.out_of_pocket, expected.out_of_pocket),
        expected=expected.out_of_pocket,
        high=max(high.out_of_pocket, expected.out_of_pocket),
        high_driver=driver,
    )


def _scheme_band(
    policy: NormalizedPolicy,
    rules,
    procedure: Procedure,
    hospital: Hospital,
    room: RoomCategory,
) -> CostBand:
    """Under a package rate there is genuinely little to vary, and saying so is
    the honest answer rather than manufacturing a spread to match the other
    path. A longer stay does not change what the family pays, because the
    package already covers it. What can change is the room upgrade, so the band
    reflects that and nothing else."""
    bad_bill, driver = adverse_bill(hospital, procedure, room)
    high = settle_under_scheme(
        policy, rules, bad_bill, procedure, hospital, room_category=room
    )
    expected = settle_under_scheme(
        policy, rules, estimate_bill(hospital, procedure, room),
        procedure, hospital, room_category=room,
    )

    return CostBand(
        low=expected.out_of_pocket,
        expected=expected.out_of_pocket,
        high=max(high.out_of_pocket, expected.out_of_pocket),
        high_driver=(
            driver if high.out_of_pocket > expected.out_of_pocket
            else "the package price does not change with a longer stay"
        ),
    )
