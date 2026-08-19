"""Stages 5 and 7: find hospitals, cost them, rank them, and never return nothing.

Three commitments shape this module.

**Exclusions are data.** Every hospital that fails a filter records why. Without
that the system cannot explain an empty result, cannot decide which constraint
to relax, and cannot tell a user "there are four cardiac hospitals within your
radius but none are in your insurer's cashless network", which is far more
useful than a blank page and is exactly the situation that causes the panic the
problem statement describes.

**Ranking is multi-objective and says so.** Cheapest, nearest and best-equipped
are usually three different hospitals. Rather than hiding that behind one score,
the non-dominated set is computed first (options where nothing else is better
on every axis at once) and only then ordered by a preference the user can see
and change.

**Starvation is handled by relaxing constraints in a stated order**, cheapest
sacrifice first, with each relaxation labelled and its consequence spelled out.
Travelling further is an inconvenience; leaving the cashless network turns a
covered admission into one the family must fund upfront, so those are not
surrendered in the same breath.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.events import bus
from app.core.logging import get_logger
from app.pipeline.s6_simulate.estimate import estimate_across, estimate_for
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.hospital import Hospital
from app.schemas.match import (
    CareContext,
    Exclusion,
    ExclusionCause,
    MatchResult,
    Objectives,
    RankedOption,
    Relaxation,
    RelaxationKind,
)
from app.schemas.money import format_inr
from app.schemas.phrasing import Phrase, phrase
from app.schemas.policy import NormalizedPolicy, RoomCategory
from app.schemas.procedure import Procedure, Urgency
from app.schemas.simulation import SettlementMode

log = get_logger(__name__)
STAGE = PipelineStage.MATCH

TARGET_OPTIONS = 5
MIN_ACCEPTABLE_OPTIONS = 3
MAX_CANDIDATES_TO_COST = 40
"""Costing every hospital in a city is wasted work; the geographically and
capability-filtered set is already ranked well enough to truncate."""

# Rough city driving speed, used to turn distance into something a caregiver
# can act on. Deliberately pessimistic, Indian metro traffic is the norm.
CITY_SPEED_KMH = 18.0

CITYWIDE_RADIUS_KM = 30.0
"""What "we looked further" widens to. Covers a metro end to end."""


@dataclass
class _Filters:
    """The constraints in force for one attempt at matching."""

    max_distance_km: float
    require_cashless: bool
    require_bed_availability: bool
    room_ceiling: RoomCategory | None
    allow_government: bool = True
    relaxations: list[Relaxation] = field(default_factory=list)


def travel_minutes(distance_km: float) -> int:
    return max(1, round(distance_km / CITY_SPEED_KMH * 60))


def _filter_hospitals(
    hospitals: list[Hospital],
    context: CareContext,
    policy: NormalizedPolicy,
    filters: _Filters,
) -> tuple[list[tuple[Hospital, float]], list[Exclusion]]:
    """Apply the current constraints, recording why each rejection happened."""
    kept: list[tuple[Hospital, float]] = []
    excluded: list[Exclusion] = []

    def drop(hospital: Hospital, cause: ExclusionCause, detail: str = "") -> None:
        excluded.append(Exclusion(
            hospital_id=hospital.hospital_id, hospital_name=hospital.name,
            cause=cause, detail=detail,
        ))

    for hospital in hospitals:
        distance = context.origin.distance_km(hospital.location)
        if distance > filters.max_distance_km:
            drop(hospital, ExclusionCause.TOO_FAR, f"{distance:.1f} km away")
            continue

        if context.procedure_code and not hospital.performs(context.procedure_code):
            drop(hospital, ExclusionCause.PROCEDURE_UNAVAILABLE)
            continue

        if context.specialty and context.specialty.value not in hospital.specialties:
            drop(hospital, ExclusionCause.SPECIALTY_UNAVAILABLE)
            continue

        if (
            filters.require_cashless
            and context.insurer_id
            and not hospital.is_cashless_for(context.insurer_id)
        ):
            drop(hospital, ExclusionCause.NOT_CASHLESS)
            continue

        rooms = _eligible_rooms(hospital, policy, filters)
        if not rooms:
            drop(hospital, ExclusionCause.NO_ELIGIBLE_ROOM)
            continue

        if filters.require_bed_availability and not any(r.has_availability for r in rooms):
            drop(hospital, ExclusionCause.NO_BED_AVAILABLE)
            continue

        kept.append((hospital, distance))

    return kept, excluded


def _eligible_rooms(hospital: Hospital, policy: NormalizedPolicy, filters: _Filters):
    ceiling = filters.room_ceiling or policy.room_limit.category_ceiling
    rooms = [
        t for t in hospital.room_tariffs
        if t.category is not RoomCategory.ICU
        and (ceiling is None or t.category.is_within(ceiling))
    ]
    return rooms


def _choose_room(
    hospital: Hospital,
    policy: NormalizedPolicy,
    context: CareContext,
    filters: _Filters,
) -> RoomCategory | None:
    """Pick the room this hospital would be booked into.

    Defaults to the best room that still sits under the policy's daily cap, so
    the recommendation does not silently put the patient into a proportionate
    deduction. Where nothing fits, the cheapest room is taken and the cost
    engine reports the consequence rather than the matcher hiding it.
    """
    if context.preferred_room and hospital.tariff_for(context.preferred_room):
        return context.preferred_room

    rooms = _eligible_rooms(hospital, policy, filters)
    available = [r for r in rooms if r.has_availability] or rooms
    if not available:
        return None

    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    if cap is not None:
        within = [r for r in available if r.per_day <= cap]
        if within:
            return max(within, key=lambda r: r.category.rank).category

    return min(available, key=lambda r: r.per_day).category


def _estimate(
    policy: NormalizedPolicy,
    hospital: Hospital,
    procedure: Procedure,
    room: RoomCategory,
    context: CareContext,
    *,
    is_network: bool,
    with_band: bool = True,
):
    """One entry point, so a second policy cannot be honoured in the headline
    figure and forgotten in the counterfactual beside it."""
    second = _second_policy.get(policy.policy_id)
    if second is not None:
        return estimate_across(
            [policy, second], hospital, procedure, room,
            is_network=is_network, patient_age=context.patient_age,
        )
    return estimate_for(
        policy, hospital, procedure, room, is_network=is_network,
        with_band=with_band, patient_age=context.patient_age,
    )


# Keyed on the leading policy for the duration of one search. Passing it down
# through six signatures that do not otherwise care about it would be worse.
_second_policy: dict[str, NormalizedPolicy] = {}


def _cost_option(
    hospital: Hospital,
    distance: float,
    procedure: Procedure,
    policy: NormalizedPolicy,
    context: CareContext,
    filters: _Filters,
) -> RankedOption | None:
    room = _choose_room(hospital, policy, context, filters)
    if room is None:
        return None

    is_network = (
        hospital.is_cashless_for(context.insurer_id) if context.insurer_id else True
    )

    try:
        # One entry point, so a scheme beneficiary is costed as a scheme
        # beneficiary here and everywhere else that asks the same question.
        result = _estimate(
            policy, hospital, procedure, room, context, is_network=is_network,
        )
    except ValueError:
        return None

    return RankedOption(
        hospital=hospital,
        simulation=result,
        distance_km=round(distance, 2),
        objectives=Objectives(affordability=0, capability=0, proximity=0, cashless=0),
        score=0.0,
    )


# How much of the ranking urgency is allowed to move. Enough to reorder options
# that are close, not enough to override a preference the user set deliberately:
# somebody who asked to protect their money in an emergency still meant it.
_URGENCY_PROXIMITY_SHIFT: dict[Urgency, float] = {
    Urgency.EMERGENCY: 0.25,
    Urgency.URGENT: 0.10,
    Urgency.PLANNED: 0.0,
}


def _weights_for(context: CareContext) -> dict[str, float]:
    """The preference, tilted towards getting there when time is short.

    Urgency used to change one filter and nothing else, so an emergency and a
    planned admission produced identical rankings. Distance is the thing that
    actually changes meaning between the two: forty minutes across a city is an
    inconvenience when the procedure is three weeks away and a different kind of
    problem when it is tonight.
    """
    weights = dict(context.preference.weights)
    shift = _URGENCY_PROXIMITY_SHIFT.get(context.urgency, 0.0)
    if shift <= 0:
        return weights

    # Taken from the money-shaped objectives rather than from capability. A
    # hospital that cannot perform the procedure well is not a faster option.
    movable = weights["affordability"] + weights["cashless"]
    taken = min(shift, movable * 0.6)
    weights["proximity"] += taken
    weights["affordability"] -= taken * (weights["affordability"] / movable)
    weights["cashless"] -= taken * (weights["cashless"] / movable)
    return weights


def _score(options: list[RankedOption], context: CareContext) -> None:
    """Normalise objectives across the candidate set and apply the preference.

    Normalisation is relative to the options actually available, so "affordable"
    means affordable among these hospitals rather than against an abstract scale
    the user cannot see.
    """
    if not options:
        return

    costs = [float(o.simulation.out_of_pocket) for o in options]
    distances = [o.distance_km for o in options]
    lo_cost, hi_cost = min(costs), max(costs)
    lo_dist, hi_dist = min(distances), max(distances)

    def invert(value: float, low: float, high: float) -> float:
        # Lower is better for cost and distance; flip into 0-1 where 1 is best.
        if high <= low:
            return 1.0
        return round(1.0 - (value - low) / (high - low), 4)

    weights = _weights_for(context)
    for option in options:
        option.objectives = Objectives(
            affordability=invert(float(option.simulation.out_of_pocket), lo_cost, hi_cost),
            capability=option.hospital.quality.capability_score,
            proximity=invert(option.distance_km, lo_dist, hi_dist),
            cashless=(
                1.0 if option.simulation.settlement_mode is SettlementMode.CASHLESS
                else 0.25
            ),
        )
        option.score = option.objectives.score(weights)

    frontier = pareto_frontier(options)
    frontier_ids = {id(o) for o in frontier}
    for option in options:
        option.on_pareto_frontier = id(option) in frontier_ids


def pareto_frontier(options: list[RankedOption]) -> list[RankedOption]:
    """Options that nothing else beats on every objective simultaneously."""
    return [
        option for option in options
        if not any(
            other is not option and other.objectives.dominates(option.objectives)
            for other in options
        )
    ]


def _explain(
    option: RankedOption,
    options: list[RankedOption],
    policy: NormalizedPolicy,
    context: CareContext,
) -> None:
    """Attach the reasoning a user needs to disagree with the ranking."""
    result = option.simulation
    cheapest = min(options, key=lambda o: o.simulation.out_of_pocket)
    nearest = min(options, key=lambda o: o.distance_km)
    strongest = max(options, key=lambda o: o.hospital.quality.capability_score)

    reasons: list[Phrase] = []
    if option is cheapest:
        reasons.append(phrase("reason.cheapest", "Cheapest of the options found."))
    if option is nearest:
        minutes = str(travel_minutes(option.distance_km))
        reasons.append(phrase(
            "reason.nearest", f"Closest, about {minutes} minutes away.", n=minutes,
        ))
    if option is strongest:
        reasons.append(phrase("reason.best_equipped", "Best equipped of the options found."))
    if result.settlement_mode is SettlementMode.CASHLESS:
        reasons.append(phrase(
            "reason.cashless", "Cashless: your insurer pays the hospital directly.",
        ))
    if option.hospital.quality.accreditation.is_nabh_tier:
        reasons.append(phrase(
            "reason.accredited",
            f"{option.hospital.quality.accreditation.label}.",
            accreditation=option.hospital.quality.accreditation.label,
        ))
    if not reasons:
        reasons.append(phrase(
            "reason.balanced",
            f"Balances cost and travel: {format_inr(result.out_of_pocket)} to "
            f"you, {option.distance_km:.0f} km away.",
            amount=format_inr(result.out_of_pocket),
            km=f"{option.distance_km:.0f}",
        ))

    tradeoffs: list[Phrase] = []
    if result.settlement_mode is SettlementMode.REIMBURSEMENT:
        tradeoffs.append(phrase(
            "tradeoff.pay_first",
            f"You would pay {format_inr(result.cash_to_arrange_upfront)} here "
            f"and claim it back later.",
            amount=format_inr(result.cash_to_arrange_upfront),
        ))
    if option is not cheapest:
        extra = result.out_of_pocket - cheapest.simulation.out_of_pocket
        if extra > 0:
            tradeoffs.append(phrase(
                "tradeoff.costlier",
                f"{format_inr(extra)} more than the cheapest found.",
                amount=format_inr(extra),
            ))
    if option is not nearest:
        tradeoffs.append(phrase(
            "tradeoff.further",
            f"{option.distance_km:.0f} km away, further than the nearest.",
            km=f"{option.distance_km:.0f}",
        ))

    option.reasons = reasons[:3]
    option.tradeoffs = tradeoffs[:2]
    option.counterfactual = _counterfactual(option, policy, context)


def _counterfactual(
    option: RankedOption, policy: NormalizedPolicy, context: CareContext
) -> Phrase | None:
    """A concrete, costed alternative at this same hospital.

    Room choice is the one lever a family actually controls at admission, and
    the one whose cost is least obvious, so it is quantified rather than
    described.
    """
    hospital = option.hospital
    current = option.simulation.room_category
    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)

    cheaper = [
        t for t in hospital.room_tariffs
        if t.category is not RoomCategory.ICU and t.category.rank < current.rank
    ]
    if not cheaper:
        return None

    best_saving = None
    for tariff in sorted(cheaper, key=lambda t: -t.category.rank):
        try:
            # No band here: this is a comparison between two rooms, and costing
            # both ends of both of them triples the work to change nothing.
            alternative = _estimate(
                policy, hospital,
                _procedure_cache[option.simulation.procedure_code],
                tariff.category, context,
                is_network=(
                    option.simulation.settlement_mode is SettlementMode.CASHLESS
                ),
                with_band=False,
            )
        except (ValueError, KeyError):
            continue
        saving = option.simulation.out_of_pocket - alternative.out_of_pocket
        if saving > 0 and (best_saving is None or saving > best_saving[0]):
            best_saving = (saving, tariff.category, alternative)

    if best_saving is None:
        return None

    saving, category, _ = best_saving
    if cap is not None and option.simulation.bill.room_rate_per_day > cap:
        return phrase(
            "counterfactual.within_cap",
            f"A {category.label.lower()} here would save about "
            f"{format_inr(saving)}, by staying inside the {format_inr(cap)} a "
            f"day you are covered for.",
            room=category.label, amount=format_inr(saving),
            cap=format_inr(cap), room_key=category.value,
        )
    return phrase(
        "counterfactual.saving",
        f"A {category.label.lower()} here would save about {format_inr(saving)}.",
        room=category.label, amount=format_inr(saving), room_key=category.value,
    )


_procedure_cache: dict[str, Procedure] = {}


_RELAXATIONS: dict[RelaxationKind, tuple[str, str]] = {
    RelaxationKind.WIDER_RADIUS: (
        "We searched a wider area.",
        "You would travel further.",
    ),
    RelaxationKind.ROOM_CATEGORY: (
        "We included rooms above your entitlement.",
        "A room above your limit also cuts what is paid on other charges. The "
        "cost shown already includes that.",
    ),
    RelaxationKind.BED_AVAILABILITY: (
        "We included hospitals with no free bed now.",
        "Call ahead: a bed may not be free when you arrive.",
    ),
    RelaxationKind.NON_NETWORK: (
        "We included hospitals outside your cashless network.",
        "You would pay the whole bill there and claim it back, so the full "
        "amount has to be found upfront.",
    ),
}


# What is surrendered, in what order, and what is not surrendered at all.
#
# This used to be one fixed ladder and urgency set a single flag, so switching a
# planned angioplasty to an emergency changed nothing anyone could see. Worse,
# a planned procedure three weeks out was told we had relaxed bed availability
# and left the cashless network on its behalf, neither of which anyone planning
# ahead needs or wants.
#
# What a family can afford to give up depends entirely on how much time they
# have. In an emergency, getting treated tonight beats every financial
# consideration, so the network goes early. Planning ahead, the opposite holds:
# there is time to travel and time to wait for a bed, and leaving the cashless
# network is a decision about money that should be made last or not at all.
RELAXATION_ORDER: dict[Urgency, list[RelaxationKind]] = {
    Urgency.EMERGENCY: [
        RelaxationKind.WIDER_RADIUS,
        RelaxationKind.ROOM_CATEGORY,
        RelaxationKind.NON_NETWORK,
    ],
    Urgency.URGENT: [
        RelaxationKind.WIDER_RADIUS,
        RelaxationKind.ROOM_CATEGORY,
        RelaxationKind.BED_AVAILABILITY,
        RelaxationKind.NON_NETWORK,
    ],
    Urgency.PLANNED: [
        RelaxationKind.WIDER_RADIUS,
        RelaxationKind.ROOM_CATEGORY,
        RelaxationKind.NON_NETWORK,
    ],
}
"""Ordered least costly first, per urgency.

An emergency never relaxes bed availability: a hospital with no free bed is not
an option when the patient is in the car. A planned admission never relaxes it
either, for the opposite reason, that waiting a week for a bed is a normal thing
to do and does not need to be presented as a sacrifice.
"""


def _ladder_for(urgency: Urgency) -> list[tuple[RelaxationKind, str, str]]:
    return [
        (kind, *_RELAXATIONS[kind])
        for kind in RELAXATION_ORDER.get(urgency, RELAXATION_ORDER[Urgency.PLANNED])
    ]


def _apply_relaxation(filters: _Filters, kind: RelaxationKind, context: CareContext) -> bool:
    """Loosen one constraint. Returns whether anything actually changed."""
    if kind is RelaxationKind.WIDER_RADIUS:
        # Widen to a genuinely city-wide search in one move. Scaling by a
        # multiple of the original fails exactly when it is needed most: a user
        # who asked for 500 metres gets stretched to two kilometres, which in
        # any Indian metro still reaches nothing.
        widened = max(context.max_distance_km * 4, CITYWIDE_RADIUS_KM)
        if filters.max_distance_km >= widened:
            return False
        filters.max_distance_km = widened
        return True
    if kind is RelaxationKind.ROOM_CATEGORY:
        if filters.room_ceiling is None:
            return False
        filters.room_ceiling = None
        return True
    if kind is RelaxationKind.BED_AVAILABILITY:
        if not filters.require_bed_availability:
            return False
        filters.require_bed_availability = False
        return True
    if kind is RelaxationKind.NON_NETWORK:
        if not filters.require_cashless:
            return False
        filters.require_cashless = False
        return True
    return False


def find_options(
    hospitals: list[Hospital],
    procedures: dict[str, Procedure],
    policy: NormalizedPolicy,
    context: CareContext,
    *,
    session_id: str | None = None,
    limit: int = TARGET_OPTIONS,
    second_policy: NormalizedPolicy | None = None,
) -> MatchResult:
    """Find, cost, rank and explain hospital options, relaxing only as needed."""
    _procedure_cache.update(procedures)
    if second_policy is not None:
        _second_policy[policy.policy_id] = second_policy
    else:
        _second_policy.pop(policy.policy_id, None)

    procedure = procedures.get(context.procedure_code or "")
    if procedure is None:
        bus.publish(
            STAGE, "find_options", status=EventStatus.FAILED,
            summary="No treatment selected", session_id=session_id,
        )
        return MatchResult(context=context, message=phrase(
            "search.no_treatment", "Please choose a treatment first."))

    filters = _Filters(
        max_distance_km=context.max_distance_km,
        require_cashless=context.require_cashless and bool(context.insurer_id),
        # In an emergency a free bed now matters more than anything else, and
        # waiting for a preferred hospital is not an option.
        require_bed_availability=(
            context.require_bed_availability or context.urgency is Urgency.EMERGENCY
        ),
        room_ceiling=policy.room_limit.category_ceiling,
    )

    kept, excluded = [], []
    # What gets given up, and in what order, depends on how much time there is.
    ladder = iter(_ladder_for(context.urgency))

    with bus.step(
        STAGE, "find_options", session_id=session_id,
        summary=f"Looking for hospitals that can treat {procedure.name.lower()}",
        procedure=procedure.code, radius_km=context.max_distance_km,
    ) as step:
        while True:
            kept, excluded = _filter_hospitals(hospitals, context, policy, filters)
            if len(kept) >= MIN_ACCEPTABLE_OPTIONS:
                break

            relaxed = False
            for kind, description, consequence in ladder:
                if _apply_relaxation(filters, kind, context):
                    filters.relaxations.append(Relaxation(
                        kind=kind, description=description, consequence=consequence
                    ))
                    relaxed = True
                    break
            if not relaxed:
                break

        step.add(
            considered=len(hospitals),
            matched=len(kept),
            excluded=len(excluded),
            relaxations=[r.kind.name for r in filters.relaxations],
        )
        if filters.relaxations:
            step.warn(
                f"{len(kept)} hospital{'s' if len(kept) != 1 else ''} found after "
                f"relaxing {len(filters.relaxations)} requirement"
                f"{'s' if len(filters.relaxations) != 1 else ''}"
            )
        else:
            step.ok(f"{len(kept)} hospital{'s' if len(kept) != 1 else ''} match everything you asked for")

    if not kept:
        return MatchResult(
            context=context, exclusions=excluded, considered_count=len(hospitals),
            relaxations=filters.relaxations,
            message=_starved_message(excluded, procedure),
        )

    # Cost the nearest slice rather than the whole city.
    kept.sort(key=lambda pair: pair[1])
    options: list[RankedOption] = []
    with bus.step(
        STAGE, "estimate_costs", session_id=session_id,
        summary=f"Estimating your costs at {min(len(kept), MAX_CANDIDATES_TO_COST)} hospitals",
    ) as step:
        for hospital, distance in kept[:MAX_CANDIDATES_TO_COST]:
            option = _cost_option(hospital, distance, procedure, policy, context, filters)
            if option is not None:
                options.append(option)
        step.ok(f"Costed {len(options)} option{'s' if len(options) != 1 else ''}")

    if not options:
        return MatchResult(
            context=context, exclusions=excluded, considered_count=len(hospitals),
            relaxations=filters.relaxations,
            message=phrase(
                "search.no_estimate",
                "We found hospitals but could not estimate costs for them.",
            ),
        )

    with bus.step(
        STAGE, "rank_options", session_id=session_id,
        summary=f"Ranking by: {context.preference.label.lower()}",
    ) as step:
        _score(options, context)
        options.sort(key=lambda o: (not o.on_pareto_frontier, -o.score))
        chosen = options[:limit]
        for position, option in enumerate(chosen, start=1):
            option.rank = position
            _explain(option, chosen, policy, context)
        step.ok(
            f"{len(chosen)} option{'s' if len(chosen) != 1 else ''} shortlisted, "
            f"{sum(o.on_pareto_frontier for o in options)} genuinely non-dominated",
            frontier=sum(o.on_pareto_frontier for o in options),
        )

    return MatchResult(
        options=chosen,
        relaxations=filters.relaxations,
        exclusions=excluded,
        considered_count=len(hospitals),
        context=context,
        message=_result_message(chosen, filters.relaxations),
    )


def _result_message(
    options: list[RankedOption], relaxations: list[Relaxation]
) -> Phrase:
    if not options:
        return phrase("search.none", "We could not find a suitable hospital.")
    n = str(len(options))
    lowest = format_inr(min(o.simulation.out_of_pocket for o in options))
    lead = (
        f"{n} option{'s' if len(options) != 1 else ''} found. "
        f"Your lowest estimate is {lowest}."
    )
    if relaxations:
        return phrase(
            "search.found_relaxed",
            lead + " To find these we relaxed some of what you asked for.",
            n=n, amount=lowest,
        )
    return phrase("search.found", lead, n=n, amount=lowest)


def _starved_message(exclusions: list[Exclusion], procedure: Procedure) -> Phrase:
    """Explain an empty result in terms of what actually blocked it."""
    treatment = procedure.name.lower()
    if not exclusions:
        return phrase(
            "search.none_offering",
            f"No hospital here offers {treatment}.",
            procedure=treatment,
        )

    counts: dict[ExclusionCause, int] = {}
    for exclusion in exclusions:
        counts[exclusion.cause] = counts.get(exclusion.cause, 0) + 1
    top = max(counts, key=lambda c: counts[c])

    return phrase(
        "search.starved",
        f"No hospital met everything you asked for {treatment}. The commonest "
        f"reason was {top.label.lower()}, at {counts[top]} "
        f"hospital{'s' if counts[top] != 1 else ''}. Try a wider search area.",
        procedure=treatment, reason=top.label, reason_key=top.value,
        n=str(counts[top]),
    )
