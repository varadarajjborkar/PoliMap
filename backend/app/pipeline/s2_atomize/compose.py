"""Put a limit back together when extraction reported it in halves.

A policy that writes

    Room Rent Limit    1% of Sum Insured per day, subject to a maximum of
                       Rs. 5,000/- per day

has stated one entitlement: whichever of the two figures binds lower against
this policyholder's own sum insured. On a ₹3,00,000 cover that is ₹3,000, and
the ₹5,000 never bites; on a ₹10,00,000 cover it is ₹5,000, and the percentage
never bites. The compiler models exactly that.

Extraction can still hand back the two halves as separate clauses, because the
sentence gets cut at a chunk boundary or because a model reads the percentage
and the ceiling as two facts. Downstream that is not a small error. The
verification loop sees two room limits, correctly concludes that only one of
them can be this policyholder's term, and settles a contradiction that was
never a contradiction by discarding half of the rule. Which half survives is
arbitrary, and both outcomes are wrong in rupees.

So the halves are rejoined here, before anything reasons about conflicts. The
rejoining is deliberately hard to trigger, because the opposite mistake is
worse: fusing two limits that really were separate invents a cap the document
does not state. Four things must all hold.

* Same benefit. A room limit and an ICU limit are never two halves of one rule.
* Same page and same section. A figure in the schedule and a figure in the
  wording are two claims about the same benefit, which is a real conflict and
  belongs to the adjudicator, not here.
* Same period. A per-day percentage and a per-admission ceiling are different
  terms that happen to share a subject.
* The document says so. Either one of the quotes carries the qualifier that
  ties them together, or the two quotes sit in one sentence on the page with
  that qualifier in the text between them.

Anything short of all four is left alone and reaches verification as the
disagreement it appears to be.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.core.logging import get_logger
from app.pipeline.s2_atomize import patterns as P
from app.schemas.document import Page
from app.schemas.policy import Clause, ClauseKind

log = get_logger(__name__)

FUSABLE_KINDS = {ClauseKind.ROOM_RENT_CAP, ClauseKind.ICU_CAP}

MAX_GAP_CHARS = 90
"""How far apart two quotes may sit and still be one sentence.

Wide enough for "1% of Sum Insured per day, subject to a maximum of" plus the
whitespace an OCR pass leaves behind, narrow enough that the next row of a
benefit table cannot reach across.
"""

_SENTENCE_BREAK = re.compile(r"[.;]\s|\n\s*\n")


def _num(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _period(clause: Clause) -> bool | None:
    """Whether this clause is stated per day, where it says so."""
    if "per_day" in clause.params:
        return bool(clause.params["per_day"])
    return P.is_per_day(clause.verbatim) or None


def _same_sentence(first: Clause, second: Clause, pages: dict[int, Page]) -> bool:
    """Whether the two quotes sit in one sentence, joined by a qualifier."""
    page = pages.get(first.evidence.page_index)
    if page is None or not page.text:
        return False

    text = P.normalise_whitespace(page.text)
    left = P.normalise_whitespace(first.verbatim)
    right = P.normalise_whitespace(second.verbatim)
    at_left, at_right = text.find(left), text.find(right)
    if at_left < 0 or at_right < 0:
        return False

    # Whichever comes first, the qualifier has to be in the text between them.
    if at_left > at_right:
        at_left, at_right = at_right, at_left
        left, right = right, left
    between = text[at_left + len(left):at_right]
    if len(between) > MAX_GAP_CHARS or _SENTENCE_BREAK.search(between):
        return False
    return P.has_max_qualifier(between)


def _joined(pct: Clause, flat: Clause, *, reason: str) -> Clause:
    """One clause carrying both bounds, quoting whichever span holds them."""
    # The longer quote is the one likelier to contain the whole term, and it is
    # the quote a reader is shown when they ask where a figure came from.
    lead, other = (pct, flat) if len(pct.verbatim) >= len(flat.verbatim) else (flat, pct)
    fused = lead.model_copy(deep=True)
    fused.params = {
        "basis": "pct_with_max",
        "pct_of_si": str(pct.params["pct_of_si"]),
        "amount_inr": str(flat.params["amount_inr"]),
        "per_day": bool(pct.params.get("per_day") or flat.params.get("per_day")),
    }
    # Not raised. These are two halves of one reading, not two readings that
    # happen to agree, and there is no second opinion here to be encouraged by.
    fused.confidence = max(pct.confidence, flat.confidence)
    fused.notes = [*lead.notes, f"Read together with “{other.verbatim}”: {reason}"]
    return fused


def fuse_qualified_limits(clauses: list[Clause], pages: list[Page]) -> list[Clause]:
    """Rejoin a percentage and the ceiling stated on it, where both were split."""
    by_page = {page.page_index: page for page in pages}
    remaining = list(clauses)
    fused: list[Clause] = []

    for kind in FUSABLE_KINDS:
        candidates = [c for c in remaining if c.kind is kind]
        pcts = [c for c in candidates if c.params.get("basis") == "pct_of_si"]
        flats = [c for c in candidates if c.params.get("basis") == "flat"]
        if not pcts or not flats:
            continue

        used: set[int] = set()
        for pct in pcts:
            if _num(pct.params.get("pct_of_si")) is None:
                continue
            for flat in flats:
                if id(flat) in used:
                    continue
                if _num(flat.params.get("amount_inr")) is None:
                    continue
                if flat.evidence.page_index != pct.evidence.page_index:
                    continue
                if flat.evidence.section is not pct.evidence.section:
                    continue
                # A per-day percentage and a per-admission ceiling are two
                # terms. Unstated on either side is not a mismatch: an OCR pass
                # loses "per day" from one half of a row often enough.
                left, right = _period(pct), _period(flat)
                if left is not None and right is not None and left != right:
                    continue

                if P.has_max_qualifier(pct.verbatim) or P.has_max_qualifier(flat.verbatim):
                    reason = "the document states the second as a ceiling on the first"
                elif _same_sentence(pct, flat, by_page):
                    reason = "both were read from one sentence in the document"
                else:
                    continue

                fused.append(_joined(pct, flat, reason=reason))
                used.add(id(flat))
                used.add(id(pct))
                break

        if used:
            remaining = [c for c in remaining if id(c) not in used]

    if not fused:
        return clauses
    log.info("fused qualified limits", count=len(fused))
    return [*remaining, *fused]
