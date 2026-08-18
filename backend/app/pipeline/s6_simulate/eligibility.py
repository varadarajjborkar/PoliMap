"""Whether this policy will pay for this treatment at all.

Every other number this system produces assumes the answer is yes. A room
limit, a proportionate deduction, a co-payment and a sub-limit are all ways of
paying less; a waiting period is the way of paying nothing, and it is the one
thing a person cannot find out by reading their own schedule, because it needs
three facts held together: what the document says, when the policy started, and
what is being treated.

The document was already being read for waiting periods. They were listed on
screen and then ignored, so someone six weeks into a new policy could be shown
a hospital, a room, a co-payment and a rupee figure for an operation their
insurer would decline outright.

Two things here cannot come from the document, and both are asked rather than
guessed. Whether a condition is pre-existing is a fact about the patient. And
where the policy start date was not read, nothing at all can be judged, so the
honest output is a question rather than a reassuring silence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from app.schemas.policy import NormalizedPolicy, WaitingKind, WaitingPeriod
from app.schemas.procedure import Procedure, Specialty
from app.schemas.scheme import rules_for


class Verdict(StrEnum):
    """Ordered by how much it should stop somebody."""

    COVERED = "covered"
    ASK = "ask"
    """Settled by one answer from the user, not by reading further."""
    UNKNOWN = "unknown"
    """A fact we do not hold, most often when the policy started."""
    NOT_YET = "not_yet"
    """A waiting period that has not run out. The claim would be declined."""


_SEVERITY: dict[Verdict, int] = {
    Verdict.COVERED: 0,
    Verdict.ASK: 1,
    Verdict.UNKNOWN: 2,
    Verdict.NOT_YET: 3,
}


@dataclass
class Finding:
    verdict: Verdict
    kind: WaitingKind
    headline: str
    detail: str
    clears_on: date | None = None
    days_left: int | None = None
    question: str | None = None
    """What the user could answer to settle an ASK."""
    label: str = ""
    """Shown instead of the kind's own name where the finding is not about a
    waiting period. Set only by findings that need it."""
    clause_ids: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.label or self.kind.label


@dataclass
class Assessment:
    verdict: Verdict
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocks(self) -> bool:
        """Whether a claim would be refused outright as things stand."""
        return self.verdict is Verdict.NOT_YET

    @property
    def headline(self) -> str:
        return self.findings[0].headline if self.findings else "Covered"

    def of(self, kind: WaitingKind) -> Finding | None:
        return next((f for f in self.findings if f.kind is kind), None)


# Obstetric treatment, for matching a maternity waiting period. Kept to the
# specialty rather than a word list: a maternity clause applies to the whole
# field, not to whichever procedures happen to be named in it.
_MATERNITY_SPECIALTIES = frozenset({Specialty.OBSTETRICS_GYNAECOLOGY})

# Splitting "cataract, hernia, and joint replacement" into the things it names.
_LIST_SEPARATORS = re.compile(r"\s*(?:,|;|/|\band\b|\bor\b)\s*", re.IGNORECASE)

# Words that carry no meaning on their own when matching a named list against a
# treatment. Without these, "surgery" in a clause would match every operation.
_TOO_GENERAL = frozenset(
    {
        "surgery", "surgeries", "treatment", "treatments", "procedure",
        "procedures", "disease", "diseases", "ailment", "ailments", "illness",
        "illnesses", "condition", "conditions", "specified", "listed", "the",
        "any", "all", "other", "related", "management", "care", "of", "for",
    }
)

MIN_TERM_LENGTH = 4
"""Below this a token matches too much. "eye" would catch every ophthalmic
procedure from a clause that named only one of them."""

# Phrases a policy uses for a family of treatments that the catalogue names one
# by one. A schedule says "joint replacement"; the treatment is a total knee
# replacement, and no word of the clause appears in it.
#
# Deliberately short and specific. Anything broader starts declining claims
# that would in fact be paid, which is the more damaging of the two mistakes
# this can make: someone told they are covered checks with the insurer, while
# someone told they are not may simply not go.
_FAMILIES: dict[str, tuple[str, ...]] = {
    "joint replacement": ("knee replacement", "hip replacement", "arthroplasty"),
    "joint replacement surgery": (
        "knee replacement", "hip replacement", "arthroplasty",
    ),
    "calculi": ("stone", "lithotripsy"),
    "urinary stone": ("stone", "lithotripsy"),
    "gall bladder": ("cholecystectomy", "gall bladder"),
    "internal congenital anomaly": (),
}


def _singular(word: str) -> str:
    """Crude, and enough: a clause writes "veins" where a catalogue writes "vein"."""
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def _terms_in(applies_to: str) -> list[str]:
    """The things a waiting-period clause actually names."""
    terms: list[str] = []
    for part in _LIST_SEPARATORS.split(applies_to.lower()):
        cleaned = part.strip(" .:-\t")
        if len(cleaned) < MIN_TERM_LENGTH or cleaned in _TOO_GENERAL:
            continue
        terms.append(cleaned)
    return terms


def names_this_treatment(applies_to: str, procedure: Procedure) -> bool:
    """Whether a named-treatment waiting period covers this procedure.

    Matched against the words a person would use as well as the clinical name,
    because a policy writes "piles" where the catalogue writes "haemorrhoid".
    """
    haystack = " ".join(
        [procedure.name.lower(), *(s.lower() for s in procedure.synonyms)]
    )
    singular = " ".join(_singular(word) for word in haystack.split())

    for term in _terms_in(applies_to):
        if term in haystack or term in singular:
            return True
        if any(member in singular for member in _FAMILIES.get(term, ())):
            return True
        # Every word of the clause's term appearing is enough, in any order:
        # "hernia repair" against "Inguinal hernia repair with mesh".
        words = [_singular(w) for w in term.split() if len(w) >= MIN_TERM_LENGTH]
        if words and all(word in singular for word in words):
            return True
    return False


def _shortfall(period: WaitingPeriod, start: date, on: date) -> tuple[date, int] | None:
    """When this clears and how many days remain, or nothing if it has."""
    clears = period.clears_on(start)
    if on >= clears:
        return None
    return clears, (clears - on).days


def _in_words(days: int) -> str:
    if days < 45:
        return f"{days} more day{'s' if days != 1 else ''}"
    months = round(days / 30.44)
    if months < 18:
        return f"about {months} more month{'s' if months != 1 else ''}"
    return f"about {round(months / 12, 1):g} more years"


def assess(
    policy: NormalizedPolicy,
    procedure: Procedure,
    *,
    on: date,
    pre_existing: bool | None = None,
    accident: bool = False,
) -> Assessment:
    """What stands between this policy and a claim for this treatment.

    `on` is the day of admission. `pre_existing` is the patient's answer about
    the condition being treated, and `accident` marks an admission following
    accidental injury, which the initial waiting period does not apply to.
    """
    if rules_for(policy.government_scheme) is not None:
        # Scheme cover is not underwritten per member and does not serve a
        # waiting period. An entitled family is entitled from the day the card
        # is issued, which is a real difference from a commercial policy and
        # worth saying rather than leaving as an absence.
        return Assessment(
            verdict=Verdict.COVERED,
            findings=[
                Finding(
                    verdict=Verdict.COVERED,
                    kind=WaitingKind.OTHER,
                    headline="No waiting period",
                    detail="Scheme cover applies from the day the card is issued.",
                )
            ],
        )

    findings: list[Finding] = []

    day_care = _day_care_finding(policy, procedure)
    if day_care is not None:
        findings.append(day_care)

    relevant = [
        period for period in policy.waiting_periods if _applies(period, procedure)
    ]
    if not relevant:
        return _assemble(findings)

    start = policy.meta.start_date
    if start is None:
        longest = max(relevant, key=lambda w: (w.months * 31) + w.days)
        findings.append(
            Finding(
                verdict=Verdict.UNKNOWN,
                kind=WaitingKind.OTHER,
                headline="We could not read when your policy started",
                detail=(
                    f"This policy has waiting periods of up to "
                    f"{longest.describe()}. Until we know the start date we "
                    f"cannot tell you whether they still apply."
                ),
                question="When did this policy start?",
                label="Policy start date",
                clause_ids=[cid for w in relevant for cid in w.source_clause_ids],
            )
        )
        return _assemble(findings)

    findings.extend(
        finding
        for period in relevant
        if (finding := _judge(period, procedure, start, on, pre_existing, accident))
    )
    return _assemble(findings)


def _assemble(findings: list[Finding]) -> Assessment:
    """Worst finding first, and it decides the verdict."""
    if not findings:
        return Assessment(verdict=Verdict.COVERED)
    findings.sort(key=lambda f: -_SEVERITY[f.verdict])
    return Assessment(verdict=findings[0].verdict, findings=findings)


def _day_care_finding(
    policy: NormalizedPolicy, procedure: Procedure
) -> Finding | None:
    """The twenty-four hour rule, which catches a fifth of this catalogue.

    Standard hospitalisation cover in India pays only where the patient was
    admitted for a full day. Treatment that finishes sooner is paid for only
    where the policy lists day care procedures, and a policy that says it does
    not cover them declines the claim outright, whatever the waiting periods
    say.
    """
    if not procedure.is_daycare:
        return None

    if policy.covers_daycare is True:
        return None

    if policy.covers_daycare is False:
        return Finding(
            verdict=Verdict.NOT_YET,
            kind=WaitingKind.OTHER,
            headline="Not covered: this finishes in under a day",
            detail=(
                f"{procedure.name} usually finishes inside twenty-four hours. "
                f"This policy requires a full day of admission and does not "
                f"cover day care procedures, so the claim would be declined "
                f"however long you have held it."
            ),
            label="Day care treatment",
        )

    return Finding(
        verdict=Verdict.UNKNOWN,
        kind=WaitingKind.OTHER,
        headline="Check that day care treatment is covered",
        detail=(
            f"{procedure.name} usually finishes inside twenty-four hours, and "
            f"standard cover in India requires a full day of admission. "
            f"Nothing we have says either way. Ask your insurer whether it is "
            f"on their day care list before you are admitted."
        ),
        label="Day care treatment",
    )


def _applies(period: WaitingPeriod, procedure: Procedure) -> bool:
    """Whether this period has anything to do with this treatment."""
    if period.kind in (WaitingKind.INITIAL, WaitingKind.PRE_EXISTING):
        return True
    if period.kind is WaitingKind.MATERNITY:
        return procedure.specialty in _MATERNITY_SPECIALTIES
    return names_this_treatment(period.applies_to, procedure)


def _judge(
    period: WaitingPeriod,
    procedure: Procedure,
    start: date,
    on: date,
    pre_existing: bool | None,
    accident: bool,
) -> Finding | None:
    remaining = _shortfall(period, start, on)
    if remaining is None:
        return None
    clears, days_left = remaining

    if period.kind is WaitingKind.INITIAL:
        if accident:
            return Finding(
                verdict=Verdict.COVERED,
                kind=period.kind,
                headline="Covered as accidental injury",
                detail=(
                    f"The first {period.describe()} of this policy cover only "
                    f"accidental injury, which is what this is."
                ),
                clears_on=clears,
                days_left=days_left,
                clause_ids=period.source_clause_ids,
            )
        return Finding(
            verdict=Verdict.NOT_YET,
            kind=period.kind,
            headline=f"Not covered for {_in_words(days_left)}",
            detail=(
                f"This policy started on {start:%d %B %Y}. For its first "
                f"{period.describe()} it covers accidental injury only, so a "
                f"planned admission before {clears:%d %B %Y} would be declined."
            ),
            clears_on=clears,
            days_left=days_left,
            clause_ids=period.source_clause_ids,
        )

    if period.kind is WaitingKind.PRE_EXISTING:
        if pre_existing is False:
            return None
        if pre_existing is None:
            return Finding(
                verdict=Verdict.ASK,
                kind=period.kind,
                headline="Depends on whether this condition is pre-existing",
                detail=(
                    f"Conditions that existed before this policy began are not "
                    f"covered for {period.describe()} from the start, which here "
                    f"means until {clears:%d %B %Y}. A condition that first "
                    f"appeared after the policy started is covered now."
                ),
                clears_on=clears,
                days_left=days_left,
                question=(
                    "Did you have this condition before this policy started?"
                ),
                clause_ids=period.source_clause_ids,
            )
        return Finding(
            verdict=Verdict.NOT_YET,
            kind=period.kind,
            headline=f"Pre-existing: not covered for {_in_words(days_left)}",
            detail=(
                f"A condition you had before this policy began is covered "
                f"{period.describe()} after the start date, which is "
                f"{clears:%d %B %Y}."
            ),
            clears_on=clears,
            days_left=days_left,
            clause_ids=period.source_clause_ids,
        )

    named = period.applies_to.strip().rstrip(".") or "this treatment"
    return Finding(
        verdict=Verdict.NOT_YET,
        kind=period.kind,
        headline=f"Not covered for {_in_words(days_left)}",
        detail=(
            f"This policy names {named} as waiting {period.describe()} from the "
            f"start date, so {procedure.name.lower()} is covered from "
            f"{clears:%d %B %Y}."
        ),
        clears_on=clears,
        days_left=days_left,
        clause_ids=period.source_clause_ids,
    )
