"""HTTP surface.

Reading a document runs OCR and several model calls, so that work is
pushed to a worker thread and the event loop stays free to stream progress
to the browser while it happens. That streaming is the point: the user watches the
system read their policy rather than staring at a spinner, and every step it
reports is the same `PipelineEvent` the server logged.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.agents.registry import registry
from app.api.session import DatasetMissing, Session, datasets, sessions
from app.core import artifacts
from app.core.events import bus
from app.core.logging import get_logger
from app.journey import position, tracker
from app.pipeline.run import run_policy_pipeline_bytes
from app.pipeline.s4_compile.compiler import apply_answer
from app.pipeline.s5_match.matcher import find_options, travel_minutes
from app.schemas.hospital import GeoPoint
from app.schemas.journey import JourneyStage
from app.schemas.match import CareContext, Preference
from app.schemas.money import format_inr
from app.schemas.policy import ExpenseHead, RoomCategory, RoomLimit, RoomLimitBasis
from app.schemas.procedure import Specialty, Urgency
from app.schemas.scheme import rules_for

log = get_logger(__name__)
router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _session(session_id: str) -> Session:
    try:
        return sessions.require(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found. Upload a policy first.") from None


def _apply_scheme(session: Session) -> None:
    """Stamp the chosen government scheme onto the compiled policy.

    Picking PM-JAY in the dropdown used to set an insurer id and nothing more,
    so the cost engine had no way to know it was not looking at a commercial
    policy and adjudicated it as one. That produced advice, aimed at the poorest
    users this system has, to arrange the full bill in cash and claim it back
    afterwards, when the scheme has no reimbursement route at all.

    A scheme also overrides the fields a scheme does not have. Leaving a room
    cap or a co-payment behind from a manual form would quietly reintroduce the
    deductions the scheme exists to prevent.
    """
    if session.policy is None or not session.insurer_id:
        return

    insurer = next(
        (i for i in datasets.insurers if i.insurer_id == session.insurer_id), None
    )
    if insurer is None or insurer.scheme is None:
        return

    rules = rules_for(insurer.scheme)
    if rules is None:
        return

    policy = session.policy
    policy.government_scheme = insurer.scheme.value
    policy.meta.insurer_name = insurer.name
    policy.meta.policy_type = "government scheme"

    if policy.sum_insured <= 0:
        policy.sum_insured = rules.cover_per_year

    # The package is all-inclusive, so the heads an indemnity policy strips out
    # first are the ones a scheme covers.
    policy.covers_consumables = True
    policy.copay_pct = rules.copay_pct
    policy.deductible = Decimal(0)
    policy.room_limit = RoomLimit(
        basis=RoomLimitBasis.CATEGORY_ONLY,
        category_ceiling=rules.room_entitlement,
    )
    policy.pre_hospitalisation_days = rules.pre_hospitalisation_days
    policy.post_hospitalisation_days = rules.post_hospitalisation_days


# --- health ---------------------------------------------------------------


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "dataset_built": datasets.is_built,
        "active_sessions": sessions.count(),
        "session_store": sessions.kind,
        "page_image_bytes": artifacts.disk_usage_bytes(),
    }


@router.get("/health/providers")
def provider_health() -> dict[str, Any]:
    """Which model serves each role on this account. Probes live."""
    return registry.health()


# --- reference data -------------------------------------------------------


@router.get("/reference")
def reference() -> dict[str, Any]:
    """Everything the interface needs to render its forms."""
    try:
        procedures = datasets.procedures
        insurers = datasets.insurers
        cities = datasets.cities()
    except DatasetMissing as exc:
        raise HTTPException(503, str(exc)) from exc

    return {
        "cities": cities,
        "insurers": [
            {
                "id": i.insurer_id, "name": i.name,
                "scheme": i.is_government_scheme,
                "scheme_code": i.scheme.value if i.scheme else None,
            }
            for i in insurers
        ],
        "procedures": sorted(
            (
                {
                    "code": p.code,
                    "name": p.name,
                    "specialty": p.specialty.value,
                    "specialty_label": p.specialty.label,
                    "typical_stay_days": p.typical_los_days,
                    "indicative_cost": float(p.base_rate_non_nabh),
                }
                for p in procedures.values()
            ),
            key=lambda p: (p["specialty_label"], p["name"]),
        ),
        "preferences": [
            {"value": p.value, "label": p.label} for p in Preference
        ],
        "room_categories": [
            {"value": r.value, "label": r.label} for r in RoomCategory
        ],
    }


# --- policy ingestion -----------------------------------------------------


def _policy_payload(session: Session) -> dict[str, Any]:
    policy = session.policy
    assert policy is not None
    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    scheme_rules = rules_for(policy.government_scheme)

    return {
        "session_id": session.session_id,
        "document": session.document_name,
        "read_quality": session.read_quality,
        "needed_ocr": session.needed_ocr,
        "warnings": session.warnings,
        "confidence": policy.confidence,
        "insurer_name": policy.meta.insurer_name,
        "plan_name": policy.meta.plan_name,
        "policy_number": policy.meta.policy_number,
        "policyholder": policy.meta.policyholder_name,
        "sum_insured": float(policy.sum_insured),
        "sum_insured_display": format_inr(policy.sum_insured),
        "room_limit": {
            "description": policy.room_limit.describe(policy.sum_insured),
            "daily_cap": float(cap) if cap is not None else None,
            "category_ceiling": (
                policy.room_limit.category_ceiling.value
                if policy.room_limit.category_ceiling else None
            ),
        },
        "icu_limit": policy.icu_limit.describe(policy.sum_insured),
        "copay_pct": float(policy.copay_pct),
        "deductible": float(policy.deductible),
        "covers_consumables": policy.covers_consumables,
        # A scheme settles on package rates, so the interface has to describe
        # it in those terms rather than as a cover with caps and a co-payment.
        "government_scheme": policy.government_scheme,
        "scheme_label": (
            scheme_rules.label if scheme_rules else ""
        ),
        "scheme_note": scheme_rules.note if scheme_rules else "",
        "restore_benefit": policy.restore_benefit,
        "pre_hospitalisation_days": policy.pre_hospitalisation_days,
        "post_hospitalisation_days": policy.post_hospitalisation_days,
        "sublimits": [
            {
                "label": s.label or (s.head.label if s.head else s.procedure_code),
                "amount": float(s.amount) if s.amount else None,
                "amount_display": format_inr(s.amount) if s.amount else "",
            }
            for s in policy.sublimits
        ],
        "waiting_periods": [
            {"months": w.months, "applies_to": w.applies_to}
            for w in policy.waiting_periods
        ],
        "questions": [
            {
                "id": q.request_id,
                "kind": q.clause_kind.value,
                "question": q.question,
                "help": q.help_text,
                "suggested": q.suggested_value,
                "options": q.options,
                "page": q.evidence.page_index + 1 if q.evidence else None,
            }
            for q in policy.open_clarifications
        ],
        "clauses": [
            {
                "kind": c.kind.value,
                "quote": c.verbatim,
                "page": c.evidence.page_index + 1,
                "section": c.evidence.section.value,
                "source": c.extracted_by.value,
                "confidence": c.confidence,
                "status": c.status.value,
                "notes": c.notes,
            }
            for c in policy.clauses
        ],
    }


@router.post("/policy/upload")
async def upload_policy(
    file: UploadFile = File(...),
    insurer_id: str = Form(""),
) -> dict[str, Any]:
    """Read an uploaded policy document into a compiled policy."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "That file was empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "That file is too large. The limit is 25 MB.")

    session = sessions.create()
    session.insurer_id = insurer_id
    filename = file.filename or "policy.pdf"

    try:
        # OCR and model calls are blocking and CPU-heavy; keep them off the loop
        # so progress events reach the browser while they run.
        result = await asyncio.to_thread(
            run_policy_pipeline_bytes, data, filename, session_id=session.session_id
        )
    except Exception as exc:
        log.exception("policy pipeline failed", filename=filename)
        raise HTTPException(500, f"We could not read that document: {exc}") from exc

    session.policy = result.policy
    session.document_name = filename
    session.read_quality = result.document.quality_score
    session.needed_ocr = result.document.needed_ocr
    session.warnings = result.document.warnings
    _apply_scheme(session)
    sessions.save(session)

    return _policy_payload(session)


class ManualPolicy(BaseModel):
    """Entered by hand when someone has no document to upload."""

    insurer_id: str = ""
    insurer_name: str = ""
    sum_insured: float = Field(gt=0)
    room_limit_type: str = "flat"
    room_limit_amount: float | None = None
    room_limit_pct: float | None = None
    copay_pct: float = 0
    deductible: float = 0
    covers_consumables: bool = False


@router.post("/policy/manual")
def manual_policy(payload: ManualPolicy) -> dict[str, Any]:
    from app.schemas.policy import NormalizedPolicy, PolicyMeta, RoomLimit, RoomLimitBasis

    if payload.room_limit_type == "none":
        room = RoomLimit(basis=RoomLimitBasis.NO_LIMIT)
    elif payload.room_limit_type == "pct" and payload.room_limit_pct:
        room = RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
            pct_of_si=Decimal(str(payload.room_limit_pct)),
        )
    elif payload.room_limit_amount:
        room = RoomLimit(
            basis=RoomLimitBasis.FLAT_PER_DAY,
            amount_per_day=Decimal(str(payload.room_limit_amount)),
        )
    else:
        room = RoomLimit(basis=RoomLimitBasis.NO_LIMIT)

    session = sessions.create()
    session.insurer_id = payload.insurer_id
    session.document_name = "Entered by hand"
    session.policy = NormalizedPolicy(
        meta=PolicyMeta(insurer_name=payload.insurer_name),
        sum_insured=Decimal(str(payload.sum_insured)),
        room_limit=room,
        copay_pct=Decimal(str(payload.copay_pct)),
        deductible=Decimal(str(payload.deductible)),
        covers_consumables=payload.covers_consumables,
        confidence=1.0,
    )
    _apply_scheme(session)
    sessions.save(session)
    return _policy_payload(session)


class Answer(BaseModel):
    question_id: str
    answer: Any


@router.post("/policy/{session_id}/answer")
def answer_question(session_id: str, payload: Answer) -> dict[str, Any]:
    """Fold a user's confirmation into their compiled policy."""
    session = _session(session_id)
    if session.policy is None:
        raise HTTPException(400, "No policy on this session yet.")

    session.policy = apply_answer(session.policy, payload.question_id, payload.answer)
    sessions.save(session)
    bus.publish(
        __import__("app.schemas.events", fromlist=["PipelineStage"]).PipelineStage.COMPILE,
        "user_answer", session_id=session_id,
        summary=f"You confirmed: {payload.answer}",
    )
    return _policy_payload(session)


@router.get("/policy/{session_id}")
def get_policy(session_id: str) -> dict[str, Any]:
    session = _session(session_id)
    if session.policy is None:
        raise HTTPException(404, "No policy on this session yet.")
    return _policy_payload(session)


# --- matching -------------------------------------------------------------


class SearchRequest(BaseModel):
    procedure_code: str
    lat: float
    lon: float
    city: str = ""
    max_distance_km: float = Field(default=15.0, gt=0, le=100)
    preference: Preference = Preference.BALANCED
    urgency: Urgency = Urgency.PLANNED
    require_cashless: bool = True
    preferred_room: RoomCategory | None = None


def _option_payload(option, procedure_name: str) -> dict[str, Any]:
    result = option.simulation
    return {
        "rank": option.rank,
        "hospital": {
            "id": option.hospital.hospital_id,
            "name": option.hospital.name,
            "type": option.hospital.hospital_type.label,
            "locality": option.hospital.locality,
            "city": option.hospital.city,
            "phone": option.hospital.phone,
            "accreditation": option.hospital.quality.accreditation.label,
            "beds": option.hospital.quality.bed_count,
            "icu_beds": option.hospital.quality.icu_beds,
            "specialties": len(option.hospital.specialties),
            "capability": option.hospital.quality.capability_score,
            "lat": option.hospital.location.lat,
            "lon": option.hospital.location.lon,
        },
        "distance_km": option.distance_km,
        "travel_minutes": travel_minutes(option.distance_km),
        "room": {
            "category": result.room_category.value,
            "label": result.room_category.label,
            "per_day": float(result.bill.room_rate_per_day),
            "per_day_display": format_inr(result.bill.room_rate_per_day),
        },
        "procedure": procedure_name,
        "estimated_bill": float(result.gross_total),
        "estimated_bill_display": format_inr(result.gross_total),
        "insurer_pays": float(result.payable_by_insurer),
        "insurer_pays_display": format_inr(result.payable_by_insurer),
        "you_pay": float(result.out_of_pocket),
        "you_pay_display": format_inr(result.out_of_pocket),
        "cash_upfront": float(result.cash_to_arrange_upfront),
        "cash_upfront_display": format_inr(result.cash_to_arrange_upfront),
        "settlement": result.settlement_mode.value,
        "settlement_label": result.settlement_mode.label,
        "covered_fraction": result.covered_fraction,
        "band": (
            {
                "low": float(result.band.low),
                "expected": float(result.band.expected),
                "high": float(result.band.high),
                "low_display": format_inr(result.band.low),
                "high_display": format_inr(result.band.high),
                # Without this the range is a pair of numbers a reader has no
                # reason to believe. With it, the high figure is a scenario
                # they can picture and argue with.
                "high_driver": result.band.high_driver,
            }
            if result.band else None
        ),
        "waterfall": [
            {
                "kind": step.kind.value,
                "label": step.label,
                "amount": float(step.deducted),
                "amount_display": format_inr(step.deducted),
                "payable_after": float(step.payable_after),
                "explanation": step.explanation,
                "heads": [h.label for h in step.affected_heads],
            }
            for step in result.steps
        ],
        "bill_lines": [
            {
                "head": line.head.value,
                "label": line.label,
                "amount": float(line.amount),
                "amount_display": format_inr(line.amount),
                "note": line.note,
            }
            for line in result.bill.lines
        ],
        "on_frontier": option.on_pareto_frontier,
        "score": option.score,
        "objectives": option.objectives.model_dump(),
        "reasons": option.reasons,
        "tradeoffs": option.tradeoffs,
        "counterfactual": option.counterfactual,
        "warnings": result.warnings,
        "notes": result.notes,
    }


@router.post("/search/{session_id}")
async def search(session_id: str, payload: SearchRequest) -> dict[str, Any]:
    session = _session(session_id)
    if session.policy is None or not session.policy.is_usable:
        raise HTTPException(400, "We need your cover amount before searching.")

    procedure = datasets.procedures.get(payload.procedure_code)
    if procedure is None:
        raise HTTPException(404, "Unknown treatment.")

    context = CareContext(
        procedure_code=payload.procedure_code,
        specialty=Specialty(procedure.specialty),
        urgency=payload.urgency,
        origin=GeoPoint(lat=payload.lat, lon=payload.lon),
        city=payload.city,
        max_distance_km=payload.max_distance_km,
        preference=payload.preference,
        preferred_room=payload.preferred_room,
        require_cashless=payload.require_cashless,
        insurer_id=session.insurer_id,
    )

    result = await asyncio.to_thread(
        find_options, datasets.hospitals, datasets.procedures,
        session.policy, context, session_id=session_id,
    )
    session.match = result
    sessions.save(session)

    return _search_payload(result)


_MORE_OPTIONS_ADVICE: dict[str, str] = {
    "too_far": "Widening your search area would bring in the most hospitals.",
    "procedure_unavailable": (
        "Most hospitals nearby do not perform this treatment. A wider search "
        "area is the thing most likely to help."
    ),
    "specialty_unavailable": (
        "This speciality is thinly covered near you. Try a wider search area."
    ),
    "not_cashless": (
        "Most hospitals nearby are outside your cashless network. Including "
        "them would mean paying upfront and claiming it back."
    ),
    "no_bed_available": (
        "Beds are the constraint right now rather than cover. It is worth "
        "calling the hospitals below before travelling."
    ),
    "no_eligible_room": (
        "Your room entitlement is ruling out most hospitals nearby. Accepting "
        "a higher room category would open more up, at a cost."
    ),
}


def _one_thing_to_change(result) -> str:
    """The single change that would show the user more options.

    This replaced a breakdown of every exclusion cause with its count. Nobody
    needs to be told that 341 hospitals were too far away; it is engineering
    pride rendered as a widget. What a family in a corridor can act on is one
    sentence naming the constraint that is actually binding.
    """
    summary = result.exclusion_summary()
    if not summary:
        return ""
    top = max(summary, key=lambda cause: summary[cause])
    return _MORE_OPTIONS_ADVICE.get(str(top), "")


def _search_payload(result) -> dict[str, Any]:
    code = result.context.procedure_code if result.context else None
    procedure = datasets.procedures.get(code) if code else None
    name = procedure.name if procedure else ""

    city = result.context.city if result.context else ""
    # Scoped to the city actually searched. The corpus spans four cities, so
    # reporting its full size beside a city-scoped search read as a claim that
    # Bengaluru alone holds 580 hospitals.
    in_city = sum(1 for h in datasets.hospitals if h.city == city) if city else 0

    return {
        "message": result.message,
        "fully_satisfied": result.is_fully_satisfied,
        "considered": result.considered_count,
        "considered_in_city": in_city,
        "city": city,
        "one_thing_to_change": _one_thing_to_change(result),
        "options": [_option_payload(o, name) for o in result.options],
        "relaxations": [
            {
                "kind": r.kind.name.lower(),
                "description": r.description,
                "consequence": r.consequence,
            }
            for r in result.relaxations
        ],
        "exclusions": [
            {"reason": cause, "count": count}
            for cause, count in sorted(
                result.exclusion_summary().items(), key=lambda kv: -kv[1]
            )
        ],
    }


# --- journey --------------------------------------------------------------


class StartJourney(BaseModel):
    hospital_id: str
    procedure_code: str
    room_category: RoomCategory


def _natural_next(stage: JourneyStage) -> str | None:
    """The stage that follows in sequence, which is what to preselect.

    Taking the first of an unordered set of legal moves is what produced the
    original defect: the set is alphabetical, so "discharge_planning" came out
    ahead of "investigation" and the interface proposed skipping most of the
    stay by default.
    """
    ahead = [s for s in JourneyStage if s.order > stage.order]
    return min(ahead, key=lambda s: s.order).value if ahead else None


def _position_payload(state, policy) -> dict[str, Any] | None:
    """What the charges recorded so far come to after adjudication."""
    result = position.position(state, policy)
    if result is None:
        return None

    return {
        "billed": float(result.bill.total),
        "billed_display": format_inr(result.bill.total),
        "insurer_pays": float(result.payable_by_insurer),
        "insurer_pays_display": format_inr(result.payable_by_insurer),
        "you_pay": float(result.out_of_pocket),
        "you_pay_display": format_inr(result.out_of_pocket),
        "steps": [
            {
                "label": s.label,
                "kind": s.kind.value,
                "deducted": float(s.deducted),
                "deducted_display": format_inr(s.deducted),
                "explanation": s.explanation,
            }
            for s in result.steps
        ],
        "warnings": result.warnings,
    }


def _journey_payload(session: Session) -> dict[str, Any]:
    state = session.journey
    policy = session.policy
    assert state is not None and policy is not None
    burn = tracker.burn_down(state, policy)

    return {
        "stage": state.stage.value,
        "stage_label": state.stage.label,
        "stage_order": state.stage.order,
        "hospital_name": state.hospital_name,
        "room": state.room_category.label if state.room_category else None,
        "room_rate": float(state.room_rate_per_day) if state.room_rate_per_day else None,
        "days_elapsed": state.days_elapsed,
        "pre_auth_filed": state.pre_auth_filed,
        "accrued": float(state.accrued_total),
        "accrued_display": format_inr(state.accrued_total),
        # Every stage, in order, each labelled with what moving there would
        # mean. The interface needs that to warn before a skip and to let
        # someone step back without hunting for a separate control.
        "stages": [
            {
                "value": s.value,
                "label": s.label,
                "order": s.order,
                "kind": (
                    "current" if s is state.stage
                    else tracker.classify(state.stage, s).value
                ),
                "skips": [
                    skipped.label
                    for skipped in tracker.skipped_between(state.stage, s)
                ],
            }
            for s in sorted(JourneyStage, key=lambda s: s.order)
        ],
        "next_stage": _natural_next(state.stage),
        "burn_down": {
            "sum_insured": float(burn.sum_insured),
            "consumed": float(burn.consumed),
            "remaining": float(burn.remaining),
            "remaining_display": format_inr(burn.remaining),
            "projected": float(burn.projected_total),
            "consumed_fraction": burn.consumed_fraction,
            "will_exceed": burn.will_exceed,
            # From the recurring charges only. A theatre bill on day one is not
            # a daily rate, and projecting it as one is how a family gets told
            # their cover runs out tomorrow when it does not.
            "daily_run_rate": float(tracker.daily_run_rate(state)),
            "daily_run_rate_display": format_inr(tracker.daily_run_rate(state)),
            "days_of_cover_left": tracker.days_until_cover_exhausted(state, policy),
        },
        # The same waterfall that produced the estimate, run over what has
        # actually been billed. Without it this screen shows the hospital's
        # total and the previous screen shows the family's, and they disagree.
        "position": _position_payload(state, policy),
        "alerts": [
            {
                "kind": a.kind.value,
                "severity": a.severity.value,
                "title": a.title,
                "message": a.message,
                "action": a.action,
                "amount": float(a.amount) if a.amount is not None else None,
                "amount_display": format_inr(a.amount) if a.amount is not None else "",
            }
            for a in state.active_alerts
        ],
        "timeline": [
            {
                "id": e.event_id,
                "at": e.at.isoformat(),
                "stage": e.stage.value,
                "title": e.title,
                "description": e.description,
                "alert_count": len(e.alerts),
                "kind": e.kind.value,
                "skipped": [s.label for s in e.skipped],
                "reason": e.reason,
            }
            for e in state.timeline
        ],
        "costs": [
            {
                "id": c.entry_id,
                "head": c.head.label,
                "head_value": c.head.value,
                "amount": float(c.amount),
                "amount_display": format_inr(c.amount),
                "description": c.description,
                "at": c.recorded_at.isoformat(),
                "receipt_name": c.receipt_name,
            }
            for c in state.costs
        ],
    }


@router.post("/journey/{session_id}/start")
def start_journey(session_id: str, payload: StartJourney) -> dict[str, Any]:
    session = _session(session_id)
    if session.policy is None:
        raise HTTPException(400, "No policy on this session yet.")

    hospital = next(
        (h for h in datasets.hospitals if h.hospital_id == payload.hospital_id), None
    )
    if hospital is None:
        raise HTTPException(404, "Unknown hospital.")

    tariff = hospital.tariff_for(payload.room_category)
    session.journey = tracker.start_journey(
        session.policy,
        session_id=session_id,
        hospital_id=hospital.hospital_id,
        hospital_name=hospital.name,
        procedure_code=payload.procedure_code,
        room_category=payload.room_category,
        room_rate_per_day=tariff.per_day if tariff else None,
    )
    sessions.save(session)
    return _journey_payload(session)


class Advance(BaseModel):
    stage: JourneyStage
    note: str = ""
    confirm_skip: bool = False
    """Set once the user has been told which stages are being passed over."""
    reason: str = Field(default="", max_length=600)
    """Why they skipped, in their own words. Never required."""


@router.post("/journey/{session_id}/advance")
def advance_journey(session_id: str, payload: Advance) -> dict[str, Any]:
    session = _session(session_id)
    if session.journey is None or session.policy is None:
        raise HTTPException(400, "No journey started yet.")

    try:
        tracker.advance(
            session.journey, payload.stage, session.policy,
            note=payload.note, reason=payload.reason, force=payload.confirm_skip,
        )
    except tracker.TransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    sessions.save(session)
    return _journey_payload(session)


# --- charges ---------------------------------------------------------------

MAX_RECEIPT_BYTES = 10 * 1024 * 1024
RECEIPT_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}


def _store_receipt(session_id: str, entry_id: str, upload: UploadFile) -> str:
    """Save a bill photograph next to the charge it belongs to.

    The stored name is the entry id, so nothing a user typed reaches the
    filesystem. The original name is kept in the entry itself, for display.
    """
    original = Path(upload.filename or "receipt")
    suffix = original.suffix.lower()
    if suffix not in RECEIPT_SUFFIXES:
        raise HTTPException(
            400,
            "Attach a PDF or a photo of the bill "
            "(PDF, JPG, PNG, WEBP, HEIC or TIFF).",
        )

    data = upload.file.read()
    if len(data) > MAX_RECEIPT_BYTES:
        raise HTTPException(413, "That file is too large. The limit is 10 MB.")
    if not data:
        raise HTTPException(400, "That file was empty.")

    target = artifacts.receipt_dir(session_id) / f"{entry_id}{suffix}"
    target.write_bytes(data)
    return original.name


@router.post("/journey/{session_id}/cost")
async def record_cost(
    session_id: str,
    head: ExpenseHead = Form(...),
    amount: float = Form(...),
    description: str = Form(""),
    advance_day: bool = Form(False),
    receipt: UploadFile | None = File(None),
) -> dict[str, Any]:
    """Record a charge, optionally with a photograph of the bill.

    Multipart rather than JSON because of that attachment. Chasing paper
    receipts weeks later at claim time is the part people dread, so the moment
    to capture one is while they are holding it.
    """
    session = _session(session_id)
    if session.journey is None or session.policy is None:
        raise HTTPException(400, "No journey started yet.")
    if amount <= 0:
        raise HTTPException(400, "Enter an amount greater than zero.")

    if advance_day:
        session.journey.days_elapsed += 1

    entry = tracker.record_cost(
        session.journey, head, Decimal(str(amount)),
        session.policy, description=description,
    )

    if receipt is not None and receipt.filename:
        entry.receipt_name = _store_receipt(session_id, entry.entry_id, receipt)

    sessions.save(session)
    return _journey_payload(session)


class UpdateCost(BaseModel):
    """Every field optional: only what was sent is changed."""

    head: ExpenseHead | None = None
    amount: float | None = Field(default=None, gt=0)
    at: datetime | None = None
    description: str | None = None


@router.patch("/journey/{session_id}/cost/{entry_id}")
def update_cost(session_id: str, entry_id: str, payload: UpdateCost) -> dict[str, Any]:
    session = _session(session_id)
    if session.journey is None or session.policy is None:
        raise HTTPException(400, "No journey started yet.")

    try:
        tracker.update_cost(
            session.journey, entry_id, session.policy,
            head=payload.head,
            amount=Decimal(str(payload.amount)) if payload.amount is not None else None,
            recorded_at=payload.at,
            description=payload.description,
        )
    except tracker.CostNotFound:
        raise HTTPException(404, "That charge is no longer on this stay.") from None

    sessions.save(session)
    return _journey_payload(session)


@router.delete("/journey/{session_id}/cost/{entry_id}")
def delete_cost(session_id: str, entry_id: str) -> dict[str, Any]:
    session = _session(session_id)
    if session.journey is None or session.policy is None:
        raise HTTPException(400, "No journey started yet.")

    try:
        tracker.remove_cost(session.journey, entry_id, session.policy)
    except tracker.CostNotFound:
        raise HTTPException(404, "That charge is no longer on this stay.") from None

    # The bill photograph goes with the charge it documented.
    for path in artifacts.receipt_dir(session_id).glob(f"{entry_id}.*"):
        path.unlink(missing_ok=True)

    sessions.save(session)
    return _journey_payload(session)


@router.get("/journey/{session_id}/cost/{entry_id}/receipt")
def get_receipt(session_id: str, entry_id: str) -> FileResponse:
    """Serve back the attached bill so the user can check what they filed."""
    _session(session_id)
    matches = sorted(artifacts.receipt_dir(session_id).glob(f"{entry_id}.*"))
    if not matches:
        raise HTTPException(404, "No receipt was attached to that charge.")
    return FileResponse(matches[0])


@router.post("/journey/{session_id}/preauth")
def file_preauth(session_id: str) -> dict[str, Any]:
    session = _session(session_id)
    if session.journey is None or session.policy is None:
        raise HTTPException(400, "No journey started yet.")
    session.journey.pre_auth_filed = True
    session.journey.active_alerts = tracker.evaluate(session.journey, session.policy)
    sessions.save(session)
    bus.publish(
        __import__("app.schemas.events", fromlist=["PipelineStage"]).PipelineStage.JOURNEY,
        "preauth_filed", session_id=session_id,
        summary="Pre-authorisation filed with the insurer",
    )
    return _journey_payload(session)


@router.get("/journey/{session_id}")
def get_journey(session_id: str) -> dict[str, Any]:
    session = _session(session_id)
    if session.journey is None:
        raise HTTPException(404, "No journey started yet.")
    return _journey_payload(session)


# --- session ---------------------------------------------------------------


@router.get("/session/{session_id}")
def restore_session(session_id: str) -> dict[str, Any]:
    """Everything needed to put the interface back where the user left it.

    The browser remembers only the session id. On a reload, or on following a
    link straight to a later step, this returns the work already done so the
    user is not sent back to the upload screen with their document read and
    their results thrown away.
    """
    session = _session(session_id)
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "policy": _policy_payload(session) if session.policy else None,
        "search": _search_payload(session.match) if session.match else None,
        "journey": (
            _journey_payload(session)
            if session.journey and session.policy else None
        ),
        "search_context": (
            session.match.context.model_dump(mode="json")
            if session.match and session.match.context else None
        ),
    }


@router.get("/session/{session_id}/export")
def export_session(session_id: str) -> dict[str, Any]:
    """The whole session as plain JSON, for the browser to keep.

    The browser, not this server, is the durable copy. Sessions here expire on a
    timer and a container restart takes the file with it, so a stay tracked over
    five days would not survive on the server alone. The client stores what this
    returns and hands it back through `import` when the server no longer has it.
    """
    session = _session(session_id)
    return {"snapshot": json.loads(session.to_json())}


class SessionImport(BaseModel):
    snapshot: dict[str, Any]


@router.post("/session/import")
def import_session(payload: SessionImport) -> dict[str, Any]:
    """Rebuild a session the server has forgotten, from the browser's copy.

    A fresh id is issued rather than reusing the one in the snapshot. The old id
    may still exist here under a different state, and quietly overwriting it
    would let one restored tab clobber another that is genuinely live.

    Page images are not part of the snapshot and are not restored: they are
    pictures of someone's insurance document and keeping them past their session
    is not a trade worth making. Evidence crops degrade to the quoted text.
    """
    session = sessions.create()
    restored_id = session.session_id

    try:
        rebuilt = Session.from_json(json.dumps(payload.snapshot))
    except Exception as exc:
        sessions.delete(restored_id)
        raise HTTPException(
            400, "That saved stay could not be read. Start a new one."
        ) from exc

    rebuilt.session_id = restored_id
    if rebuilt.journey is not None:
        # The journey carries the id it was created under, and the activity
        # stream is keyed on it. Left stale, every event from here on would be
        # published to a session nobody is listening to.
        rebuilt.journey.session_id = restored_id

    sessions.save(rebuilt)
    log.info("session restored from client", session_id=restored_id)
    return restore_session(restored_id)


@router.delete("/session/{session_id}")
def clear_session(session_id: str) -> dict[str, Any]:
    """Forget a session. Backs the "start over" action in the interface."""
    sessions.delete(session_id)
    return {"cleared": True}


# --- activity stream ------------------------------------------------------


@router.get("/events/{session_id}")
async def stream_events(session_id: str, request: Request) -> StreamingResponse:
    """Server-sent stream of everything the pipeline does.

    Carries the same `PipelineEvent` objects written to the server log, so what
    the user sees cannot drift from what actually happened.
    """
    queue, backlog = bus.subscribe(replay=True, session_id=session_id)

    async def generate():
        try:
            for event in backlog:
                yield _sse(event)
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    # Comment frames keep proxies from closing an idle stream.
                    yield ": keep-alive\n\n"
                    continue
                if event.session_id in (session_id, None):
                    yield _sse(event)
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event) -> str:
    payload = {
        "id": event.event_id,
        "ts": event.ts.isoformat(),
        "stage": event.stage.value,
        "stage_label": event.stage.label,
        "step": event.step,
        "status": event.status.value,
        "summary": event.summary,
        "detail": event.detail,
        "duration_ms": event.duration_ms,
    }
    return f"data: {json.dumps(payload, default=str)}\n\n"


@router.get("/events/{session_id}/history")
def event_history(session_id: str) -> dict[str, Any]:
    """Non-streaming fallback for clients that cannot hold a connection open."""
    return {
        "events": [
            {
                "id": e.event_id,
                "ts": e.ts.isoformat(),
                "stage": e.stage.value,
                "stage_label": e.stage.label,
                "step": e.step,
                "status": e.status.value,
                "summary": e.summary,
                "detail": e.detail,
                "duration_ms": e.duration_ms,
            }
            for e in bus.history(session_id)
        ]
    }
