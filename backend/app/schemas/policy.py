"""Policy representation: the clause ledger and the compiled policy.

Two distinct shapes live here, and the distinction matters.

A `Clause` is a *raw finding*: one atomic statement lifted from a document,
carrying the exact words it came from and the pixels those words sit on. It may
be wrong, contested, or duplicated. Clauses are evidence, not truth.

A `NormalizedPolicy` is the *compiled result*: strongly typed, deduplicated,
precedence-resolved, and directly executable by the cost simulator. It is what
the rest of the system reasons about.

Keeping them apart is what lets the verification loop argue about findings
without the simulator ever seeing a half-verified number.
"""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.money import Ratio, Rupees

# ---------------------------------------------------------------------------
# Expense heads
# ---------------------------------------------------------------------------


class ExpenseHead(StrEnum):
    """A line on an Indian hospital bill.

    The split is not cosmetic: proportionate deduction applies per head, so
    getting these boundaries right is what makes the cost estimate correct.
    """

    ROOM_RENT = "room_rent"
    ICU_CHARGES = "icu_charges"
    NURSING = "nursing"
    DOCTOR_VISIT = "doctor_visit"
    SURGEON_FEE = "surgeon_fee"
    ANAESTHETIST_FEE = "anaesthetist_fee"
    OT_CHARGES = "ot_charges"
    INVESTIGATIONS = "investigations"
    PHARMACY = "pharmacy"
    CONSUMABLES = "consumables"
    IMPLANTS = "implants"
    BLOOD = "blood"
    OXYGEN = "oxygen"
    PHYSIOTHERAPY = "physiotherapy"
    AMBULANCE = "ambulance"
    NON_MEDICAL = "non_medical"

    @property
    def label(self) -> str:
        return _HEAD_LABELS[self]


_HEAD_LABELS: dict[ExpenseHead, str] = {
    ExpenseHead.ROOM_RENT: "Room rent",
    ExpenseHead.ICU_CHARGES: "ICU charges",
    ExpenseHead.NURSING: "Nursing charges",
    ExpenseHead.DOCTOR_VISIT: "Doctor visits",
    ExpenseHead.SURGEON_FEE: "Surgeon's fee",
    ExpenseHead.ANAESTHETIST_FEE: "Anaesthetist's fee",
    ExpenseHead.OT_CHARGES: "Operation theatre",
    ExpenseHead.INVESTIGATIONS: "Tests and scans",
    ExpenseHead.PHARMACY: "Medicines",
    ExpenseHead.CONSUMABLES: "Consumables",
    ExpenseHead.IMPLANTS: "Implants and devices",
    ExpenseHead.BLOOD: "Blood",
    ExpenseHead.OXYGEN: "Oxygen",
    ExpenseHead.PHYSIOTHERAPY: "Physiotherapy",
    ExpenseHead.AMBULANCE: "Ambulance",
    ExpenseHead.NON_MEDICAL: "Non-medical items",
}


class DeductionRegime(StrEnum):
    """Which proportionate-deduction rules apply.

    The IRDAI master circular of 29 May 2024 narrowed proportionate deduction
    to room-linked heads only. Older policies and older claim practice applied
    the ratio to the entire bill. Both are modelled so the engine can be held
    against either, and so the difference can be shown to a user.
    """

    POST_2024 = "post_2024"
    LEGACY = "legacy"


# Heads whose price genuinely varies with room category, and which the post-2024
# rules therefore leave subject to proportionate deduction. ICU is excluded by
# name in the circular; pharmacy, implants, consumables and diagnostics cost the
# same whichever room the patient is in.
_ROOM_LINKED_POST_2024: frozenset[ExpenseHead] = frozenset(
    {
        ExpenseHead.ROOM_RENT,
        ExpenseHead.NURSING,
        ExpenseHead.DOCTOR_VISIT,
        ExpenseHead.SURGEON_FEE,
        ExpenseHead.ANAESTHETIST_FEE,
        ExpenseHead.OT_CHARGES,
        ExpenseHead.BLOOD,
        ExpenseHead.OXYGEN,
        ExpenseHead.PHYSIOTHERAPY,
    }
)

# Never reimbursable under any regime: the IRDAI non-payable list.
_NEVER_PAYABLE: frozenset[ExpenseHead] = frozenset({ExpenseHead.NON_MEDICAL})


def is_room_linked(head: ExpenseHead, regime: DeductionRegime) -> bool:
    """Whether proportionate deduction touches this head."""
    if head in _NEVER_PAYABLE:
        return False
    if regime is DeductionRegime.LEGACY:
        # Legacy practice applied the ratio to everything payable.
        return True
    return head in _ROOM_LINKED_POST_2024


def is_never_payable(head: ExpenseHead) -> bool:
    return head in _NEVER_PAYABLE


# ---------------------------------------------------------------------------
# Room categories
# ---------------------------------------------------------------------------


class RoomCategory(StrEnum):
    """Room tiers, ordered cheapest to most expensive.

    Eligibility clauses are usually expressed as a ceiling ("Single Private AC
    Room or below"), so the ordering is load-bearing, not decorative.
    """

    GENERAL_WARD = "general_ward"
    TWIN_SHARING = "twin_sharing"
    SINGLE_PRIVATE = "single_private"
    DELUXE = "deluxe"
    SUITE = "suite"
    ICU = "icu"

    @property
    def rank(self) -> int:
        return _ROOM_RANKS[self]

    @property
    def label(self) -> str:
        return _ROOM_LABELS[self]

    def is_within(self, ceiling: RoomCategory) -> bool:
        """Whether this room is at or below an eligibility ceiling."""
        if self is RoomCategory.ICU or ceiling is RoomCategory.ICU:
            # ICU sits outside the ladder; it has its own limit.
            return True
        return self.rank <= ceiling.rank


_ROOM_RANKS: dict[RoomCategory, int] = {
    RoomCategory.GENERAL_WARD: 0,
    RoomCategory.TWIN_SHARING: 1,
    RoomCategory.SINGLE_PRIVATE: 2,
    RoomCategory.DELUXE: 3,
    RoomCategory.SUITE: 4,
    RoomCategory.ICU: 99,
}

_ROOM_LABELS: dict[RoomCategory, str] = {
    RoomCategory.GENERAL_WARD: "General ward",
    RoomCategory.TWIN_SHARING: "Twin sharing",
    RoomCategory.SINGLE_PRIVATE: "Single private room",
    RoomCategory.DELUXE: "Deluxe room",
    RoomCategory.SUITE: "Suite",
    RoomCategory.ICU: "ICU",
}

SELECTABLE_ROOMS: tuple[RoomCategory, ...] = (
    RoomCategory.GENERAL_WARD,
    RoomCategory.TWIN_SHARING,
    RoomCategory.SINGLE_PRIVATE,
    RoomCategory.DELUXE,
    RoomCategory.SUITE,
)


# ---------------------------------------------------------------------------
# The clause ledger
# ---------------------------------------------------------------------------


class ClauseKind(StrEnum):
    POLICY_META = "policy_meta"
    INSURED_PERSON = "insured_person"
    SUM_INSURED = "sum_insured"
    ROOM_RENT_CAP = "room_rent_cap"
    ICU_CAP = "icu_cap"
    ROOM_CATEGORY_ELIGIBILITY = "room_category_eligibility"
    SUBLIMIT = "sublimit"
    PROCEDURE_CAP = "procedure_cap"
    COPAY = "copay"
    DEDUCTIBLE = "deductible"
    WAITING_PERIOD = "waiting_period"
    EXCLUSION = "exclusion"
    PRE_HOSPITALISATION = "pre_hospitalisation"
    POST_HOSPITALISATION = "post_hospitalisation"
    NETWORK_RULE = "network_rule"
    RESTORE_BENEFIT = "restore_benefit"
    NO_CLAIM_BONUS = "no_claim_bonus"
    CONSUMABLES_COVER = "consumables_cover"
    DAYCARE_COVER = "daycare_cover"
    AMBULANCE_COVER = "ambulance_cover"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").capitalize()


# Kinds a usable policy cannot plausibly lack. The completeness auditor hunts
# for these before the ledger is allowed to compile.
REQUIRED_CLAUSE_KINDS: frozenset[ClauseKind] = frozenset(
    {ClauseKind.SUM_INSURED, ClauseKind.ROOM_RENT_CAP}
)


class ClauseStatus(StrEnum):
    PROPOSED = "proposed"
    """Extracted, not yet examined."""
    CHALLENGED = "challenged"
    """A challenge is open against it."""
    CONFIRMED = "confirmed"
    """Survived verification."""
    REJECTED = "rejected"
    """Disproved or superseded."""
    NEEDS_USER = "needs_user"
    """Unresolvable from the document alone; only the user can settle it."""


class DocumentSection(StrEnum):
    """Where in the document a clause was found.

    A policy *schedule* carries this policyholder's actual numbers; policy
    *wording* carries generic terms that may not apply. Conflating them is the
    most common way to extract a confidently wrong figure, so provenance at this
    granularity drives precedence during compilation.
    """

    SCHEDULE = "schedule"
    WORDING = "wording"
    ENDORSEMENT = "endorsement"
    BENEFIT_TABLE = "benefit_table"
    EXCLUSIONS = "exclusions"
    UNKNOWN = "unknown"

    @property
    def precedence(self) -> int:
        """Higher wins when two clauses of the same kind conflict."""
        return _SECTION_PRECEDENCE[self]


_SECTION_PRECEDENCE: dict[DocumentSection, int] = {
    DocumentSection.ENDORSEMENT: 40,
    DocumentSection.SCHEDULE: 30,
    DocumentSection.BENEFIT_TABLE: 20,
    DocumentSection.EXCLUSIONS: 15,
    DocumentSection.WORDING: 10,
    DocumentSection.UNKNOWN: 0,
}


class BoundingBox(BaseModel):
    """Pixel rectangle on a rendered page, origin top-left."""

    x0: float
    y0: float
    x1: float
    y1: float

    def union(self, other: BoundingBox) -> BoundingBox:
        return BoundingBox(
            x0=min(self.x0, other.x0),
            y0=min(self.y0, other.y0),
            x1=max(self.x1, other.x1),
            y1=max(self.y1, other.y1),
        )

    def padded(self, pad: float) -> BoundingBox:
        return BoundingBox(
            x0=self.x0 - pad, y0=self.y0 - pad, x1=self.x1 + pad, y1=self.y1 + pad
        )


class Evidence(BaseModel):
    """Where a clause came from, precisely enough to show the user."""

    page_index: int = Field(ge=0)
    bbox: BoundingBox | None = None
    char_start: int | None = None
    char_end: int | None = None
    section: DocumentSection = DocumentSection.UNKNOWN
    ocr_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    """Mean OCR confidence over the quoted span; None when text was native."""


class ExtractorKind(StrEnum):
    GRAMMAR = "grammar"
    """Deterministic pattern rules over Indian policy idioms."""
    MODEL = "model"
    """Language model reading the page."""
    VISION = "vision"
    """Language model reading the page image."""
    USER = "user"
    """Supplied or confirmed by the person."""


class Clause(BaseModel):
    """One atomic, evidence-bearing statement lifted from a policy document."""

    model_config = ConfigDict(validate_assignment=True)

    clause_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    kind: ClauseKind
    verbatim: str
    """Exact source text. Must really occur in the document, enforced by the
    grounding check in the atomize stage, not by asking a model nicely."""

    evidence: Evidence
    params: dict[str, Any] = Field(default_factory=dict)
    """Kind-specific parsed values. Loosely typed here by design; compilation
    into `NormalizedPolicy` is where these become strongly typed."""

    scope: dict[str, Any] = Field(default_factory=dict)
    """What the clause applies to, e.g. {"head": "investigations"} or
    {"procedure_code": "CGHS-0421"}. Empty means policy-wide."""

    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: ClauseStatus = ClauseStatus.PROPOSED
    extracted_by: ExtractorKind = ExtractorKind.GRAMMAR
    round_added: int = 0
    """Which verification round produced this clause."""

    notes: list[str] = Field(default_factory=list)

    @property
    def is_admissible(self) -> bool:
        return self.status in (ClauseStatus.PROPOSED, ClauseStatus.CONFIRMED)

    def supersedes(self, other: Clause) -> bool:
        """Whether this clause should win a same-kind conflict with `other`."""
        mine = self.evidence.section.precedence
        theirs = other.evidence.section.precedence
        if mine != theirs:
            return mine > theirs
        return self.confidence > other.confidence


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


class ChallengeKind(StrEnum):
    UNIT_AMBIGUITY = "unit_ambiguity"
    """Is 5,00,000 the sum insured or something else? Lakhs or rupees?"""
    SCOPE_AMBIGUITY = "scope_ambiguity"
    """Does this co-pay apply to all claims or only some?"""
    CONTRADICTION = "contradiction"
    """Two clauses of the same kind disagree."""
    MISSING = "missing"
    """A clause that must exist was not found."""
    EVIDENCE_WEAK = "evidence_weak"
    """The quoted text does not support the parsed values."""
    IMPLAUSIBLE = "implausible"
    """Parsed value is outside any realistic range."""


class ChallengeResolution(StrEnum):
    UPHELD = "upheld"
    """The challenge succeeded; the clause was rejected or corrected."""
    DISMISSED = "dismissed"
    """The clause survived."""
    ESCALATED = "escalated"
    """Undecidable from the document; goes to the user."""
    OPEN = "open"


class Challenge(BaseModel):
    """An adversarial objection raised against one or more clauses."""

    challenge_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    kind: ChallengeKind
    clause_ids: list[str] = Field(default_factory=list)
    target_kind: ClauseKind | None = None
    """Set for MISSING challenges, which have no clause to point at."""

    question: str
    """Stated plainly enough to put in front of a user if it escalates."""

    rationale: str = ""
    resolution: ChallengeResolution = ChallengeResolution.OPEN
    resolution_note: str = ""
    winning_clause_id: str | None = None
    round_raised: int = 0

    @model_validator(mode="after")
    def _needs_a_target(self) -> Self:
        if not self.clause_ids and self.target_kind is None:
            raise ValueError("challenge must reference a clause or a missing kind")
        return self


class ClarificationRequest(BaseModel):
    """A question put to the user when the document cannot settle a point.

    Deliberately shaped for a stressed non-expert: one question, plain wording,
    a suggested answer already filled in, and the page image to look at.
    """

    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    clause_kind: ClauseKind
    question: str
    help_text: str = ""
    suggested_value: Any = None
    options: list[dict[str, Any]] = Field(default_factory=list)
    evidence: Evidence | None = None
    challenge_id: str | None = None
    answered: bool = False
    answer: Any = None

    expects: str = "amount"
    """What kind of value settles this: "amount", "percent" or "choice". Set
    from the field being asked about, never from what the user typed. An answer
    is not allowed to decide which field it lands in, which is what stops a
    typed near-miss creating a second, wrong field beside the real one."""

    allow_other: bool = True
    """Whether the offered choices can be escaped with free text. Fixed options
    assume the user's situation is one the form anticipated, and often it is
    not: their document says something none of the choices covers."""

    skippable: bool = True
    """Every question can be passed over. Someone may simply not know, and an
    interrogation that cannot be ended is one people abandon."""

    skipped: bool = False

    pending_value: Any = None
    """A reading of free text, held while the user confirms it. Nothing
    interpreted from prose is applied before they have seen it restated."""

    pending_restated: str = ""


# ---------------------------------------------------------------------------
# Compiled policy
# ---------------------------------------------------------------------------


class RoomLimitBasis(StrEnum):
    NO_LIMIT = "no_limit"
    FLAT_PER_DAY = "flat_per_day"
    PCT_OF_SI_PER_DAY = "pct_of_si_per_day"
    CATEGORY_ONLY = "category_only"


class RoomLimit(BaseModel):
    """The room entitlement, however the policy chose to express it.

    Policies mix bases freely, "1% of sum insured per day, subject to a maximum
    of Rs. 5,000" is two limits at once, so all forms are held together and
    resolved to a single effective daily figure.
    """

    basis: RoomLimitBasis = RoomLimitBasis.NO_LIMIT
    amount_per_day: Rupees | None = None
    pct_of_si: Ratio | None = None
    """Percent, 0-100."""
    category_ceiling: RoomCategory | None = None
    source_clause_ids: list[str] = Field(default_factory=list)

    def effective_daily_cap(self, sum_insured: Decimal) -> Decimal | None:
        """The binding rupee cap per day, or None when uncapped.

        Where a percentage and a flat maximum both appear, the lower binds,
        that is what "subject to a maximum of" means.
        """
        from app.schemas.money import apply_pct

        candidates: list[Decimal] = []
        if self.amount_per_day is not None:
            candidates.append(self.amount_per_day)
        if self.pct_of_si is not None:
            share = apply_pct(sum_insured, self.pct_of_si)
            # A percentage of an unknown cover is not a cap of nothing, it is
            # not a cap at all. Letting the zero win the comparison turns "1%
            # of Sum Insured, subject to a maximum of Rs. 5,000" into a room
            # entitlement of nothing at all, on a policy whose only real fault
            # is that the cover figure was not read.
            if share > 0 or not candidates:
                candidates.append(share)
        return min(candidates) if candidates else None

    def describe(self, sum_insured: Decimal) -> str:
        from app.schemas.money import format_inr

        cap = self.effective_daily_cap(sum_insured)
        if cap is None and self.category_ceiling is None:
            return "No room rent limit"
        parts = []
        if cap is not None:
            parts.append(f"{format_inr(cap)} per day")
        if self.category_ceiling is not None:
            parts.append(f"up to {self.category_ceiling.label}")
        return " · ".join(parts)


class SubLimit(BaseModel):
    """A cap on one expense head or one named procedure."""

    head: ExpenseHead | None = None
    procedure_code: str | None = None
    label: str = ""
    amount: Rupees | None = None
    pct_of_si: Ratio | None = None
    per_day: bool = False
    source_clause_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _needs_a_target_and_a_cap(self) -> Self:
        if self.head is None and self.procedure_code is None:
            raise ValueError("sub-limit must target an expense head or a procedure")
        if self.amount is None and self.pct_of_si is None:
            raise ValueError("sub-limit must carry an amount or a percentage")
        return self

    def resolve(self, sum_insured: Decimal, days: int = 1) -> Decimal:
        from app.schemas.money import apply_pct

        base = (
            self.amount
            if self.amount is not None
            else apply_pct(sum_insured, self.pct_of_si or Decimal(0))
        )
        return base * days if self.per_day else base


class WaitingKind(StrEnum):
    """What a waiting period is for, which decides whether it bites here.

    The categories are not cosmetic. Only one of them applies to everybody, one
    of them cannot be judged without asking the patient a question, and the
    rest apply only to particular treatments. Treating them alike would either
    frighten someone whose cover is fine or reassure someone whose is not.
    """

    INITIAL = "initial"
    """The first 30 days, in which nothing but accidental injury is covered."""
    PRE_EXISTING = "pre_existing"
    """Conditions the patient already had when the policy began."""
    SPECIFIC_AILMENT = "specific_ailment"
    """A named list: cataract, hernia, piles, joint replacement, and so on."""
    MATERNITY = "maternity"
    OTHER = "other"

    @property
    def label(self) -> str:
        return _WAITING_LABELS[self]


_WAITING_LABELS: dict[WaitingKind, str] = {
    WaitingKind.INITIAL: "Initial waiting period",
    WaitingKind.PRE_EXISTING: "Pre-existing conditions",
    WaitingKind.SPECIFIC_AILMENT: "Named treatments",
    WaitingKind.MATERNITY: "Maternity",
    WaitingKind.OTHER: "Waiting period",
}


class WaitingPeriod(BaseModel):
    """A period after the policy starts during which something is not covered.

    Held in the unit the document wrote it in rather than converted to one.
    The initial period is thirty days, not one month, and the difference is a
    day or two on the date it clears; a pre-existing waiting period is
    twenty-four months, not seven hundred and twenty days, and the difference
    there is five days. Both are exact when kept as written and approximate the
    moment they are normalised.
    """

    months: int = Field(default=0, ge=0)
    days: int = Field(default=0, ge=0)
    kind: WaitingKind = WaitingKind.OTHER
    applies_to: str
    """Free text as the document wrote it, e.g. "pre-existing diseases"."""
    source_clause_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _has_a_duration(self) -> Self:
        if self.months == 0 and self.days == 0:
            raise ValueError("a waiting period needs a duration")
        return self

    def clears_on(self, start: date) -> date:
        """The first day this no longer applies, counting from the policy start."""
        return add_months(start, self.months) + timedelta(days=self.days)

    def describe(self) -> str:
        if self.months and self.days:
            return f"{self.months} months and {self.days} days"
        if self.months:
            years, months = divmod(self.months, 12)
            if years and not months:
                return f"{years} year{'s' if years != 1 else ''}"
            return f"{self.months} month{'s' if self.months != 1 else ''}"
        return f"{self.days} day{'s' if self.days != 1 else ''}"

    def duration_parts(self) -> tuple[str, dict[str, str]]:
        """The same span as a unit and its numbers, rather than as English.

        "24 months" reads as English wherever it is dropped, and these spans sit
        inside sentences that are read in four other languages. Handing over the
        unit and the count instead lets the sentence be rebuilt rather than
        half-translated around a phrase nobody wrote a word for.
        """
        if self.months and self.days:
            return "months_days", {"n": str(self.months), "d": str(self.days)}
        if self.months:
            years, months = divmod(self.months, 12)
            if years and not months:
                return "years", {"n": str(years)}
            return "months", {"n": str(self.months)}
        return "days", {"n": str(self.days)}


def add_months(start: date, months: int) -> date:
    """Calendar month arithmetic, clamped to the end of a short month.

    Two years from 29 February is 28 February, not the 1st of March. Written
    out rather than pulled in, since this is the only place the project needs
    it and the rule it has to get right is one line long.
    """
    if not months:
        return start
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


class InsuredPerson(BaseModel):
    """One person named on the policy.

    Age is here because it changes the money. Co-payment is commonly imposed on
    entrants above sixty, some plans cap a senior's room entitlement, and a
    pre-existing waiting period matters far more at seventy than at thirty.
    """

    name: str = ""
    age: int | None = Field(default=None, ge=0, le=120)
    relationship: str = ""
    sum_insured: Rupees | None = None
    """Set only where a person carries their own cover rather than sharing the
    family floater."""
    source_clause_ids: list[str] = Field(default_factory=list)


class Exclusion(BaseModel):
    text: str
    category: str = ""
    source_clause_ids: list[str] = Field(default_factory=list)


class PolicyMeta(BaseModel):
    insurer_name: str = ""
    plan_name: str = ""
    policy_number: str = ""
    policyholder_name: str = ""
    policy_type: str = ""
    """e.g. individual, family floater, group, government scheme."""
    start_date: date | None = None
    end_date: date | None = None
    uin: str = ""


class NormalizedPolicy(BaseModel):
    """The standardised internal representation the whole system reasons about.

    Everything here is settled: precedence resolved, duplicates merged, user
    confirmations applied. If a value could not be settled it is absent and the
    corresponding `ClarificationRequest` is still open.
    """

    policy_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    meta: PolicyMeta = Field(default_factory=PolicyMeta)

    sum_insured: Rupees = Field(default=Decimal(0))
    sum_insured_remaining: Rupees | None = None
    """Balance after claims already made this policy year."""

    room_limit: RoomLimit = Field(default_factory=RoomLimit)
    icu_limit: RoomLimit = Field(default_factory=RoomLimit)

    copay_pct: Ratio = Field(default=Decimal(0))
    copay_above_age: int | None = Field(default=None, ge=0, le=120)
    """Where set, the co-payment falls only on members at or above this age.

    Most policies carrying a co-payment write it this way. Applied to everyone
    regardless, it takes a fifth off a child's claim on a policy where the band
    exists precisely so that it does not."""
    deductible: Rupees = Field(default=Decimal(0))

    sublimits: list[SubLimit] = Field(default_factory=list)
    waiting_periods: list[WaitingPeriod] = Field(default_factory=list)
    exclusions: list[Exclusion] = Field(default_factory=list)
    insured: list[InsuredPerson] = Field(default_factory=list)
    """Everyone named on the policy. Ages here change the money."""

    covers_consumables: bool = False
    """Consumables are excluded by default in India unless a rider is bought."""
    covers_daycare: bool | None = None
    """Whether treatment finishing inside a day is paid for at all.

    Standard hospitalisation cover in India requires twenty-four hours of
    admission, and a policy pays for anything shorter only where it lists day
    care procedures. `None` means the document did not say, which is different
    from saying no."""
    cashless_available: bool = True
    pre_hospitalisation_days: int = 0
    post_hospitalisation_days: int = 0
    restore_benefit: bool = False

    deduction_regime: DeductionRegime = DeductionRegime.POST_2024
    government_scheme: str | None = None
    """Set when this is PM-JAY, ESI, CGHS or a state scheme rather than a
    commercial policy; those settle on package rates instead of a bill."""

    clauses: list[Clause] = Field(default_factory=list)
    open_clarifications: list[ClarificationRequest] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    """Aggregate confidence in this compilation, surfaced to the user."""

    @property
    def available_cover(self) -> Decimal:
        """Cover left to spend, honouring any partial exhaustion."""
        if self.sum_insured_remaining is not None:
            return self.sum_insured_remaining
        return self.sum_insured

    @property
    def is_usable(self) -> bool:
        """Whether there is enough settled information to estimate costs."""
        return self.sum_insured > 0

    def sublimit_for(self, head: ExpenseHead) -> SubLimit | None:
        return next((s for s in self.sublimits if s.head is head), None)

    def sublimit_for_procedure(self, code: str) -> SubLimit | None:
        return next((s for s in self.sublimits if s.procedure_code == code), None)

    def clauses_of(self, kind: ClauseKind) -> list[Clause]:
        return [c for c in self.clauses if c.kind is kind and c.is_admissible]

    @property
    def oldest_age(self) -> int | None:
        """The age that decides the terms.

        A family floater is priced and conditioned on its eldest member, and it
        is the eldest who carries the age-banded co-payment and the shorter
        odds on a pre-existing condition. Where the policy names one person,
        this is simply their age.
        """
        ages = [person.age for person in self.insured if person.age is not None]
        return max(ages) if ages else None

    def copay_for(self, age: int | None) -> Decimal:
        """The co-payment share falling on a member of this age.

        An unstated age is treated as though the band applies, because the
        alternative is quietly promising somebody a claim without the deduction
        their policy imposes. The interface asks who is being treated rather
        than leaving this to a default.
        """
        if self.copay_above_age is None or age is None:
            return self.copay_pct
        return self.copay_pct if age >= self.copay_above_age else Decimal(0)

    def waiting_of(self, kind: WaitingKind) -> WaitingPeriod | None:
        """The longest waiting period of a kind, which is the one that binds."""
        matching = [w for w in self.waiting_periods if w.kind is kind]
        if not matching:
            return None
        return max(matching, key=lambda w: (w.months * 31) + w.days)
