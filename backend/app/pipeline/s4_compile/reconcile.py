"""Deciding whether several uploaded files are one policy or two.

Most people who upload more than one file are uploading one policy in pieces:
the schedule as a PDF, the wording as another, a photograph of the endorsement.
Those belong in one ledger, and merging them is the whole reason to accept more
than one file at a time.

Some are not. A family covered by a corporate policy and a personal one has two
of everything, and quietly merging them produces a policy that exists nowhere:
one document's room cap against the other's sum insured, with no clause
disagreeing loudly enough to notice. Every figure after that is wrong, and
nothing on screen says so.

The test is identity, not values. Two documents from one policy disagree all the
time, a schedule saying five lakh and the wording describing a ten lakh variant,
and that disagreement is what section precedence exists to settle. What
precedence cannot settle is two different policy numbers, two insurers, or two
policyholders, because those are not a conflict to resolve but a question to
ask.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.document import IngestedDocument
from app.schemas.policy import Clause, ClauseKind, PolicyMeta

_POLICY_NUMBER = re.compile(
    r"policy\s*(?:no|number|#)\s*[.:\-]?\s*([A-Z0-9][A-Z0-9/\- ]{5,28})",
    re.IGNORECASE,
)
_INSURER = re.compile(
    r"^([A-Z][A-Za-z&.\- ]{4,48}?(?:Insurance|Assurance|Health|General))\b",
    re.MULTILINE,
)
# The label and its value are routinely on separate lines: a schedule is a
# two-column table, and flattening it to text puts "Policyholder Name" on one
# line and the name on the next. An earlier version stopped at the end of the
# label line and captured the word "Name" as everybody's name.
_INSURED_NAME = re.compile(
    r"(?:insured\s*name"
    r"|name\s+of\s+(?:the\s+)?(?:insured|policyholder)"
    r"|policyholder(?:\s*name)?)"
    r"\s*[.:\-]?\s*\n?\s*"
    r"([A-Za-z][A-Za-z .]{2,40})",
    re.IGNORECASE,
)

_NOT_A_NAME = frozenset({
    "name", "address", "policy", "uin", "period", "date", "insured",
    "policyholder", "person", "details", "sl", "no", "number",
})


@dataclass
class DocumentIdentity:
    """What a document says about which policy it belongs to."""

    filename: str
    policy_number: str = ""
    insurer: str = ""
    policyholder: str = ""

    def is_empty(self) -> bool:
        return not (self.policy_number or self.insurer or self.policyholder)


@dataclass
class Disagreement:
    """One reason to think two files are not the same policy."""

    what: str
    """"policy number", "insurer", "policyholder"."""

    values: dict[str, str] = field(default_factory=dict)
    """Filename to the value that file carried."""

    def describe(self) -> str:
        pairs = ", ".join(
            f"{name} says {value}" for name, value in self.values.items()
        )
        return f"The {self.what} does not match: {pairs}."


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .:-")


def _normalise(value: str) -> str:
    """Compare on substance, so spacing and case do not invent a conflict."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def identify(document: IngestedDocument) -> DocumentIdentity:
    """Read the few fields that say which policy a document belongs to.

    Deliberately regex rather than a model call. This runs once per uploaded
    file before anything else, the fields are printed in a small number of
    standard forms, and a wrong answer here would split one policy in two or
    merge two into one.
    """
    # The front matter is where identity lives; scanning the whole wording
    # picks up examples and specimen numbers from the terms and conditions.
    head = "\n".join(page.text for page in document.pages[:2])[:6000]

    number = _POLICY_NUMBER.search(head)
    insurer = _INSURER.search(head)
    holder = _INSURED_NAME.search(head)

    name = _clean(holder.group(1)) if holder else ""
    # A capture that is only a field label is a miss, not a name, and letting
    # one through would make every document agree on a policyholder called
    # "Name" and stop the check ever firing.
    if name.split(" ")[0].lower() in _NOT_A_NAME:
        name = ""

    return DocumentIdentity(
        filename=document.filename,
        policy_number=_clean(number.group(1)) if number else "",
        insurer=_clean(insurer.group(1)) if insurer else "",
        policyholder=name,
    )


def disagreements(identities: list[DocumentIdentity]) -> list[Disagreement]:
    """Every identity field on which the uploaded files do not agree.

    A field is only compared across the documents that carry it. A wording
    document usually names no policyholder, and treating that silence as a
    disagreement would flag every ordinary two-file upload.
    """
    found: list[Disagreement] = []

    for attribute, label in (
        ("policy_number", "policy number"),
        ("insurer", "insurer"),
        ("policyholder", "policyholder"),
    ):
        stated = {
            identity.filename: getattr(identity, attribute)
            for identity in identities
            if getattr(identity, attribute)
        }
        if len(stated) < 2:
            continue
        if len({_normalise(value) for value in stated.values()}) > 1:
            found.append(Disagreement(what=label, values=stated))

    return found


def looks_like_two_policies(identities: list[DocumentIdentity]) -> bool:
    """Whether to stop and ask rather than merge.

    A mismatched policy number alone is enough: it is the field that exists
    precisely to tell two policies apart. Insurer or policyholder alone is
    weaker, since a wording document may name a group company or a spouse, so
    those have to disagree together before the merge is held.
    """
    found = {d.what for d in disagreements(identities)}
    if "policy number" in found:
        return True
    return {"insurer", "policyholder"} <= found


def merge_clauses(per_document: list[list[Clause]]) -> list[Clause]:
    """Pool clauses from several files of the same policy into one ledger.

    Nothing is deduplicated here. Two documents stating the same room cap is
    corroboration, and the compiler already resolves competing clauses by
    section precedence, which is exactly the machinery this needs. Removing
    duplicates first would throw away the evidence that they agreed.
    """
    return [clause for clauses in per_document for clause in clauses]


def meta_from(identities: list[DocumentIdentity], existing: PolicyMeta) -> PolicyMeta:
    """Fill in identity fields from whichever document stated them."""
    for identity in identities:
        if identity.policy_number and not existing.policy_number:
            existing.policy_number = identity.policy_number
        if identity.insurer and not existing.insurer_name:
            existing.insurer_name = identity.insurer
        if identity.policyholder and not existing.policyholder_name:
            existing.policyholder_name = identity.policyholder
    return existing


def conflict_question(found: list[Disagreement]) -> str:
    """What to put in front of the user when the files do not agree."""
    reasons = " ".join(d.describe() for d in found)
    return (
        f"These files look like two different policies. {reasons} "
        f"Which one should we use for this stay?"
    )


CLAUSE_KINDS_WORTH_MERGING = frozenset({
    ClauseKind.SUM_INSURED,
    ClauseKind.ROOM_RENT_CAP,
    ClauseKind.ICU_CAP,
    ClauseKind.COPAY,
    ClauseKind.DEDUCTIBLE,
    ClauseKind.SUBLIMIT,
})
"""The kinds where a second document genuinely adds something. Used only for
reporting what a merge contributed, never to filter the ledger itself."""
