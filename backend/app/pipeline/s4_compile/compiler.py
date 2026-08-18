"""Stage 4: compile a verified clause ledger into an executable policy.

The ledger is evidence: overlapping, sometimes contradictory, carrying claims of
varying authority. The cost engine needs the opposite: one settled, strongly
typed answer per question. This stage performs that collapse, and it is the only
place allowed to choose between competing clauses.

Resolution is by declared precedence rather than by confidence alone. A figure
printed on the policyholder's own schedule outranks the same figure in generic
wording even when the wording was read more cleanly, because the schedule is
what they actually bought. Confidence only breaks ties within a tier.

Anything that cannot be settled becomes a `ClarificationRequest` rather than a
default. Silently assuming a missing co-payment is zero produces an estimate
that is too good and a user who discovers the truth at the billing counter.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.events import bus
from app.core.logging import get_logger
from app.pipeline.s4_compile.interpret import interpret
from app.schemas.events import PipelineStage
from app.schemas.money import format_inr
from app.schemas.policy import (
    ClarificationRequest,
    Clause,
    ClauseKind,
    ClauseStatus,
    Exclusion,
    ExpenseHead,
    InsuredPerson,
    NormalizedPolicy,
    PolicyMeta,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
    SubLimit,
    WaitingKind,
    WaitingPeriod,
)

log = get_logger(__name__)
STAGE = PipelineStage.COMPILE

# Below this a clause is reported to the user for confirmation rather than
# simply believed. Tuned so a clean schedule read passes untouched while a
# hedged wording clause or a poor OCR read always asks.
CONFIRM_BELOW = 0.55


def _num(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _winner(clauses: list[Clause], kind: ClauseKind) -> Clause | None:
    """The single clause that should decide this question."""
    candidates = [c for c in clauses if c.kind is kind and c.is_admissible]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda c: (c.evidence.section.precedence, c.confidence, -c.round_added),
    )


def _room_limit_from(clause: Clause | None) -> RoomLimit:
    if clause is None:
        return RoomLimit()

    params = clause.params
    basis = params.get("basis", "flat")
    amount = _num(params.get("amount_inr"))
    pct = _num(params.get("pct_of_si"))
    category = params.get("category")

    if basis == "no_limit":
        return RoomLimit(basis=RoomLimitBasis.NO_LIMIT, source_clause_ids=[clause.clause_id])
    if basis == "category" and category:
        return RoomLimit(
            basis=RoomLimitBasis.CATEGORY_ONLY,
            category_ceiling=RoomCategory(category),
            source_clause_ids=[clause.clause_id],
        )
    if basis == "pct_with_max":
        return RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
            pct_of_si=pct, amount_per_day=amount,
            source_clause_ids=[clause.clause_id],
        )
    if basis == "pct_of_si" and pct is not None:
        return RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=pct,
            source_clause_ids=[clause.clause_id],
        )
    if amount is not None:
        return RoomLimit(
            basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=amount,
            source_clause_ids=[clause.clause_id],
        )
    return RoomLimit()


# What kind of value settles each question. Taken from the field, never from
# what the user typed: an answer is not allowed to choose which field it lands
# in, which is what stops a typed near-miss creating a second, wrong field.
_EXPECTS: dict[ClauseKind, str] = {
    ClauseKind.SUM_INSURED: "amount",
    ClauseKind.ROOM_RENT_CAP: "amount",
    ClauseKind.ICU_CAP: "amount",
    ClauseKind.COPAY: "percent",
    ClauseKind.DEDUCTIBLE: "amount",
}


def _ask(
    kind: ClauseKind, question: str, *, help_text: str = "",
    suggested: object = None, clause: Clause | None = None,
    options: list[dict] | None = None,
) -> ClarificationRequest:
    return ClarificationRequest(
        clause_kind=kind,
        question=question,
        help_text=help_text,
        suggested_value=suggested,
        options=options or [],
        evidence=clause.evidence if clause else None,
        expects=_EXPECTS.get(kind, "amount"),
    )


def compile_policy(
    clauses: list[Clause], *, session_id: str | None = None
) -> NormalizedPolicy:
    """Collapse the ledger into the settled policy the engine executes."""
    with bus.step(
        STAGE, "compile_policy", session_id=session_id,
        summary="Building your coverage profile",
    ) as step:
        policy = NormalizedPolicy()
        asks: list[ClarificationRequest] = []

        # --- sum insured: nothing downstream works without it ---
        si_clause = _winner(clauses, ClauseKind.SUM_INSURED)
        si = _num(si_clause.params.get("amount_inr")) if si_clause else None
        if si is not None:
            policy.sum_insured = si
        if si is None:
            asks.append(_ask(
                ClauseKind.SUM_INSURED,
                "What is the total cover amount on your policy?",
                help_text="This is the maximum your insurer will pay in a year. "
                          "It is usually the largest figure on your policy schedule.",
            ))
        elif si_clause and si_clause.confidence < CONFIRM_BELOW:
            asks.append(_ask(
                ClauseKind.SUM_INSURED,
                f"Is your total cover {format_inr(si)}?",
                help_text="We read this from your document but could not be sure.",
                suggested=float(si), clause=si_clause,
            ))

        # --- room entitlement ---
        room_clause = _winner(clauses, ClauseKind.ROOM_RENT_CAP) or _winner(
            clauses, ClauseKind.ROOM_CATEGORY_ELIGIBILITY
        )
        policy.room_limit = _room_limit_from(room_clause)
        policy.icu_limit = _room_limit_from(_winner(clauses, ClauseKind.ICU_CAP))

        if room_clause is None:
            asks.append(_ask(
                ClauseKind.ROOM_RENT_CAP,
                "Does your policy limit how much it pays for your hospital room?",
                help_text="Most policies cap the daily room rent, either as a rupee "
                          "amount or as a percentage of your cover. This matters a "
                          "lot: a room above your limit reduces what your insurer "
                          "pays on other charges too.",
                options=[
                    {"label": "No limit on my room", "value": "none"},
                    {"label": "A fixed amount per day", "value": "flat"},
                    {"label": "A percentage of my cover", "value": "pct"},
                    {"label": "I do not know", "value": "unknown"},
                ],
            ))
        elif room_clause.confidence < CONFIRM_BELOW:
            cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
            asks.append(_ask(
                ClauseKind.ROOM_RENT_CAP,
                f"Is your room rent limit {policy.room_limit.describe(policy.sum_insured)}?"
                if cap else "Is this your room entitlement?",
                help_text=(
                    "We found this in the policy wording rather than your schedule, "
                    "so it may describe a standard plan rather than yours."
                    if room_clause.notes else
                    "We read this from your document but could not be sure."
                ),
                suggested=float(cap) if cap else None, clause=room_clause,
            ))

        # --- shares the policyholder bears ---
        copay_clause = _winner(clauses, ClauseKind.COPAY)
        if copay_clause and (pct := _num(copay_clause.params.get("pct"))) is not None:
            policy.copay_pct = pct
            band = copay_clause.params.get("above_age")
            policy.copay_above_age = int(band) if band else None
            if copay_clause.confidence < CONFIRM_BELOW and pct > 0:
                asks.append(_ask(
                    ClauseKind.COPAY,
                    f"Do you pay a {pct:g}% share of every claim?",
                    help_text="A co-payment is the part of every approved claim you "
                              "pay yourself.",
                    suggested=float(pct), clause=copay_clause,
                ))

        deductible_clause = _winner(clauses, ClauseKind.DEDUCTIBLE)
        if deductible_clause:
            amount = _num(deductible_clause.params.get("amount_inr"))
            if amount is not None:
                policy.deductible = amount

        # --- windows and flags ---
        for kind, attr in (
            (ClauseKind.PRE_HOSPITALISATION, "pre_hospitalisation_days"),
            (ClauseKind.POST_HOSPITALISATION, "post_hospitalisation_days"),
        ):
            clause = _winner(clauses, kind)
            if clause and (days := clause.params.get("days")) is not None:
                setattr(policy, attr, int(days))

        consumables = _winner(clauses, ClauseKind.CONSUMABLES_COVER)
        if consumables is not None:
            policy.covers_consumables = bool(consumables.params.get("covered"))

        daycare = _winner(clauses, ClauseKind.DAYCARE_COVER)
        if daycare is not None:
            policy.covers_daycare = bool(daycare.params.get("covered"))

        restore = _winner(clauses, ClauseKind.RESTORE_BENEFIT)
        if restore is not None:
            policy.restore_benefit = bool(restore.params.get("available"))

        # --- multi-valued groups ---
        policy.sublimits = _compile_sublimits(clauses)
        policy.waiting_periods = _compile_waiting_periods(clauses)
        policy.exclusions = [
            Exclusion(text=c.verbatim, source_clause_ids=[c.clause_id])
            for c in clauses
            if c.kind is ClauseKind.EXCLUSION and c.is_admissible
        ]
        policy.meta = _compile_meta(clauses)
        policy.insured = _compile_insured(clauses)

        policy.clauses = clauses
        policy.open_clarifications = asks
        policy.confidence = _overall_confidence(clauses, asks)

        summary = (
            f"Cover {format_inr(policy.sum_insured)}, "
            f"room {policy.room_limit.describe(policy.sum_insured)}"
        )
        if asks:
            step.warn(
                f"{summary}, {len(asks)} thing"
                f"{'s' if len(asks) != 1 else ''} to confirm with you",
                sum_insured=float(policy.sum_insured),
                clarifications=len(asks),
                confidence=policy.confidence,
            )
        else:
            step.ok(
                summary,
                sum_insured=float(policy.sum_insured),
                sublimits=len(policy.sublimits),
                confidence=policy.confidence,
            )

    return policy


def _compile_sublimits(clauses: list[Clause]) -> list[SubLimit]:
    """One cap per head or procedure, the tightest winning.

    Where two clauses cap the same head differently the lower is taken: an
    estimate that overstates cover is the one that hurts, and the conservative
    reading is also the likelier reading of a document that says both.
    """
    best: dict[tuple, tuple[Decimal, Clause]] = {}

    for clause in clauses:
        if clause.kind is not ClauseKind.SUBLIMIT or not clause.is_admissible:
            continue
        amount = _num(clause.params.get("amount_inr"))
        if amount is None:
            continue

        head_value = clause.scope.get("head") or clause.params.get("head")
        code = clause.scope.get("procedure_code") or clause.params.get("procedure_code")
        if not head_value and not code:
            continue

        key = ("head", head_value) if head_value else ("code", code)
        current = best.get(key)
        if current is None or amount < current[0]:
            best[key] = (amount, clause)

    limits: list[SubLimit] = []
    for (kind, value), (amount, clause) in best.items():
        try:
            limits.append(SubLimit(
                head=ExpenseHead(value) if kind == "head" else None,
                procedure_code=None if kind == "head" else value,
                label=clause.scope.get("label", ""),
                amount=amount,
                source_clause_ids=[clause.clause_id],
            ))
        except ValueError:
            log.debug("unknown sub-limit target", value=value)
    return limits


# What a waiting period is for, read off the words the document used. The
# order matters: "pre-existing" wins over a list that happens to mention it,
# and the initial period is recognised by what it excludes rather than by its
# length, because a policy is free to write it as 15 or 45 days.
_WAITING_KINDS: list[tuple[re.Pattern[str], WaitingKind]] = [
    (re.compile(r"pre[- ]?exist|\bPED\b", re.IGNORECASE), WaitingKind.PRE_EXISTING),
    (re.compile(r"matern|pregnan|childbirth|delivery", re.IGNORECASE),
     WaitingKind.MATERNITY),
    (re.compile(r"all\s+(?:illness|disease|ailment)|any\s+(?:illness|disease)|"
                r"other\s+than\s+accident|except\s+accident|initial",
                re.IGNORECASE), WaitingKind.INITIAL),
    (re.compile(r"cataract|hernia|joint\s+replace|piles|fistula|fissure|sinus|"
                r"tonsil|hysterec|calcul|stone|varicose|gall\s*bladder|"
                r"specified\s+(?:disease|ailment|illness)|listed\s+(?:disease|ailment)",
                re.IGNORECASE), WaitingKind.SPECIFIC_AILMENT),
]


def classify_waiting(applies_to: str, *, days: int, months: int) -> WaitingKind:
    """Which sort of waiting period this is.

    Falls back on the duration only when the words say nothing: a period
    written in days and applying to something unnamed is the initial one, since
    no other kind is ever that short.
    """
    for pattern, kind in _WAITING_KINDS:
        if pattern.search(applies_to):
            return kind
    if days and not months:
        return WaitingKind.INITIAL
    return WaitingKind.OTHER


def _compile_waiting_periods(clauses: list[Clause]) -> list[WaitingPeriod]:
    seen: dict[tuple, WaitingPeriod] = {}
    for clause in clauses:
        if clause.kind is not ClauseKind.WAITING_PERIOD or not clause.is_admissible:
            continue
        months = int(clause.params.get("months") or 0)
        days = int(clause.params.get("days") or 0)
        if not months and not days:
            continue
        applies = str(clause.params.get("applies_to") or "unspecified")
        key = (months, days, applies.lower()[:40])
        seen.setdefault(key, WaitingPeriod(
            months=months, days=days,
            kind=classify_waiting(applies, days=days, months=months),
            applies_to=applies,
            source_clause_ids=[clause.clause_id],
        ))

    # The model extractor reports a duration it found without always reporting
    # what it applies to, so a schedule row read by both extractors arrives as
    # "24 months, cataract and hernia" and "24 months, unspecified". They are
    # the same clause. Keeping both would list every waiting period twice and
    # leave half of them uncategorised, which reads as a policy with twice as
    # many restrictions as it has.
    specified = {
        (w.months, w.days) for w in seen.values() if not _is_vague(w.applies_to)
    }
    kept = [
        w for w in seen.values()
        if not (_is_vague(w.applies_to) and (w.months, w.days) in specified)
    ]
    return sorted(kept, key=lambda w: (w.months * 31) + w.days)


_VAGUE = frozenset({"", "unspecified", "not specified", "n/a", "na", "-"})


def _is_vague(applies_to: str) -> bool:
    return applies_to.strip().lower() in _VAGUE


def _compile_insured(clauses: list[Clause]) -> list[InsuredPerson]:
    """Everyone the schedule names, in the order it named them.

    Ages are the reason this exists. A family floater is conditioned on its
    eldest member, and whether a pre-existing waiting period is a formality or
    the whole question depends on who is being admitted.
    """
    people: dict[tuple[str, str], InsuredPerson] = {}
    for clause in clauses:
        if clause.kind is not ClauseKind.INSURED_PERSON or not clause.is_admissible:
            continue
        name = str(clause.params.get("name") or "").strip()
        if not name:
            continue
        age = clause.params.get("age")
        cover = clause.params.get("sum_insured")
        # Keyed on the relationship as well as the name, because a father and a
        # son sharing one are two people, and merging them would drop whichever
        # age the terms are actually conditioned on.
        key = (name.lower(), str(clause.params.get("relationship") or "").lower())
        person = people.get(key)
        if person is None:
            people[key] = InsuredPerson(
                name=name,
                age=int(age) if age is not None else None,
                relationship=str(clause.params.get("relationship") or ""),
                sum_insured=Decimal(str(cover)) if cover else None,
                source_clause_ids=[clause.clause_id],
            )
        elif person.age is None and age is not None:
            person.age = int(age)
            person.source_clause_ids.append(clause.clause_id)
    return list(people.values())


_DATE_FIELDS = frozenset({"start_date", "end_date"})


def _compile_meta(clauses: list[Clause]) -> PolicyMeta:
    meta = PolicyMeta()
    for clause in clauses:
        if clause.kind is not ClauseKind.POLICY_META or not clause.is_admissible:
            continue
        field = clause.scope.get("field") or clause.params.get("field")
        value = str(clause.params.get("value", "")).strip()
        if not field or not value or not hasattr(meta, field):
            continue
        if getattr(meta, field):
            continue
        if field in _DATE_FIELDS:
            # These are dates, not strings. Assignment on a Pydantic model does
            # not coerce by default, so an ISO string put here unchecked would
            # sit in a date field and fail the first time anything did
            # arithmetic on it, several stages away from the cause.
            try:
                setattr(meta, field, date.fromisoformat(value))
            except ValueError:
                log.warning("unreadable policy date", field=field, value=value[:40])
            continue
        setattr(meta, field, value)

    # A period that runs backwards is a misread, not a policy.
    if meta.start_date and meta.end_date and meta.end_date <= meta.start_date:
        meta.end_date = None
    return meta


def _overall_confidence(
    clauses: list[Clause], asks: list[ClarificationRequest]
) -> float:
    """How much of this compilation the user should be shown as settled.

    Weighted toward the clauses that drive money: a perfectly read policy
    number does not offset an uncertain room limit.
    """
    weights = {
        ClauseKind.SUM_INSURED: 3.0,
        ClauseKind.ROOM_RENT_CAP: 3.0,
        ClauseKind.ROOM_CATEGORY_ELIGIBILITY: 2.0,
        ClauseKind.COPAY: 2.0,
        ClauseKind.DEDUCTIBLE: 1.5,
        ClauseKind.ICU_CAP: 1.0,
        ClauseKind.SUBLIMIT: 1.0,
    }
    scored = [
        (weights[c.kind], c.confidence)
        for c in clauses
        if c.kind in weights and c.is_admissible
    ]
    if not scored:
        return 0.0

    total_weight = sum(w for w, _ in scored)
    base = sum(w * c for w, c in scored) / total_weight
    # Each open question is a known gap and should show as one.
    return round(max(0.0, min(1.0, base - 0.08 * len(asks))), 3)


# Restored when a user rejects our reading of what they typed. Held here rather
# than on the request so the wording is one thing in one place.
_ORIGINAL_QUESTIONS: dict[ClauseKind, str] = {
    ClauseKind.SUM_INSURED: "What is the total cover amount on your policy?",
    ClauseKind.ROOM_RENT_CAP: (
        "Does your policy limit how much it pays for your hospital room?"
    ),
    ClauseKind.COPAY: "What share of each claim do you pay yourself?",
}


def _looks_like_a_value(text: str) -> bool:
    """Whether this is a plain value the existing paths already handle.

    Bare digits, and the fixed option values the interface sends back, need no
    interpretation. Everything else is prose and goes through the interpreter,
    which is what makes "about five lakh" an acceptable answer.
    """
    stripped = text.strip()
    if not stripped:
        return True
    if stripped in ("none", "no", "flat", "pct", "unknown", "yes"):
        return True
    try:
        float(stripped.replace(",", ""))
    except ValueError:
        return False
    return True


def skip_question(policy: NormalizedPolicy, request_id: str) -> NormalizedPolicy:
    """Pass over a question the user cannot answer.

    Not the same as answering it. The clause stays unconfirmed and the overall
    confidence still reflects that we do not know, so the interface can go on
    saying so. What changes is that we stop asking, because an interrogation
    with no exit is one people abandon halfway through.
    """
    for request in policy.open_clarifications:
        if request.request_id == request_id:
            request.skipped = True
            request.answered = True

    policy.open_clarifications = [
        r for r in policy.open_clarifications if not r.answered
    ]
    policy.confidence = _overall_confidence(policy.clauses, policy.open_clarifications)
    return policy


def _interpret_free_text(
    policy: NormalizedPolicy, request: ClarificationRequest, text: str
) -> NormalizedPolicy | None:
    """Read prose into a value, or turn it into a confirmation question.

    Returns None when the text settled cleanly and the caller should carry on
    applying it. Returns the policy when the question has been replaced by
    something the user has to answer next, which is either a confirmation of
    what we understood or a note that we did not understand at all.

    Nothing a model interpreted is applied before the user has seen it restated.
    A paraphrase becoming a settled number without them looking at it is exactly
    how a near-miss turns into a wrong figure that nobody catches.
    """
    reading = interpret(request.question, text, expects=request.expects)
    best = reading.best

    if best is None:
        request.help_text = reading.reason or request.help_text
        policy.confidence = _overall_confidence(
            policy.clauses, policy.open_clarifications
        )
        return policy

    if best.is_none:
        request.answer = "none"
        return None

    if reading.needs_confirmation:
        request.pending_value = str(best.value)
        request.pending_restated = best.restated
        request.question = f"Did you mean {best.restated}?"
        request.help_text = reading.reason
        request.options = [
            {"label": f"Yes, {best.restated}", "value": f"__confirm__{best.value}"},
            {"label": "No, let me type it again", "value": "__retry__"},
        ]
        policy.confidence = _overall_confidence(
            policy.clauses, policy.open_clarifications
        )
        return policy

    request.answer = str(best.value)
    return None


def apply_answer(
    policy: NormalizedPolicy, request_id: str, answer: object
) -> NormalizedPolicy:
    """Fold a user's confirmation back into the compiled policy."""
    request = next(
        (r for r in policy.open_clarifications if r.request_id == request_id), None
    )
    if request is None:
        return policy

    text = answer if isinstance(answer, str) else ""

    # A rejected confirmation reopens the question rather than settling it.
    if text == "__retry__":
        request.pending_value = None
        request.pending_restated = ""
        request.question = _ORIGINAL_QUESTIONS.get(
            request.clause_kind, request.question
        )
        request.options = []
        request.help_text = "Write it however it appears on your document."
        return policy

    if text.startswith("__confirm__"):
        answer = text.removeprefix("__confirm__")
    elif text and not _looks_like_a_value(text):
        # Free text, either typed into "Other" or into the amount box. Nothing
        # is applied until it has been read into a value we can name back.
        replaced = _interpret_free_text(policy, request, text)
        if replaced is not None:
            return replaced
        answer = request.answer

    request.answered = True
    request.answer = answer

    if request.clause_kind is ClauseKind.SUM_INSURED:
        if (value := _num(answer)) is not None:
            policy.sum_insured = value
    elif request.clause_kind is ClauseKind.COPAY:
        if (value := _num(answer)) is not None:
            policy.copay_pct = value
    elif request.clause_kind is ClauseKind.ROOM_RENT_CAP:
        if answer in ("none", "no", False):
            policy.room_limit = RoomLimit(basis=RoomLimitBasis.NO_LIMIT)
        elif (value := _num(answer)) is not None:
            policy.room_limit = RoomLimit(
                basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=value
            )

    # A user's own answer is authoritative; the clause it replaces is settled.
    for clause in policy.clauses:
        if clause.kind is request.clause_kind and clause.status is ClauseStatus.NEEDS_USER:
            clause.status = ClauseStatus.CONFIRMED

    policy.open_clarifications = [
        r for r in policy.open_clarifications if not r.answered
    ]
    policy.confidence = _overall_confidence(policy.clauses, policy.open_clarifications)
    return policy
