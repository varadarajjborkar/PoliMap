"""Evidence grounding: the rule that a clause must quote text that really exists.

This is the system's structural defence against a model inventing a number, and
it is enforced in code rather than requested in a prompt. A clause is admissible
only if the text it claims to quote can be located in the page it claims to come
from. A model may still misread a figure that is genuinely present, which is
what the verification loop is for, but it cannot manufacture one out of nothing
and have it reach the user.

Matching has to tolerate OCR damage without becoming so loose that it accepts
anything. Exact matching would reject correct quotes from a photographed page,
where "Rs. 5,000" routinely comes back as "Rs. 5,OOO". So the check falls back to
an approximate match over a sliding window, with a threshold high enough that
unrelated text cannot pass.

Digits are treated more strictly than letters. A letter confused by OCR is
usually harmless, but a digit that does not appear in the source is the exact
failure this module exists to catch, so a quote whose digits are absent from the
page is rejected however well its words score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

FUZZY_THRESHOLD = 0.82
"""Similarity a quote must reach against some window of the page."""

MIN_QUOTE_CHARS = 6

# Characters OCR routinely confuses, folded together before comparison.
_OCR_FOLD = str.maketrans({
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "I": "1", "l": "1", "|": "1", "i": "1",
    "S": "5", "s": "5",
    "B": "8",
    "Z": "2", "z": "2",
    # Dash and quote variants, written as escapes because they are data rather
    # than prose: a printed en dash has to match a hyphen in the quote a clause
    # claims to have read, or grounding rejects a clause that is actually fine.
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2010": "-",  # hyphen
    "\u2018": "", "\u2019": "",  # single curly quotes
    "\u201c": "", "\u201d": "",  # double curly quotes
    '"': "",
})


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    score: float
    matched_text: str = ""
    reason: str = ""


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _fold(text: str) -> str:
    """Collapse OCR-confusable characters so damaged text still compares."""
    return normalise(text).translate(_OCR_FOLD)


def digits_of(text: str) -> str:
    return re.sub(r"\D", "", text)


def check(quote: str, source: str, *, threshold: float = FUZZY_THRESHOLD) -> GroundingResult:
    """Whether `quote` genuinely occurs in `source`."""
    if not quote or len(quote.strip()) < MIN_QUOTE_CHARS:
        return GroundingResult(False, 0.0, reason="quote too short to verify")
    if not source:
        return GroundingResult(False, 0.0, reason="no source text")

    needle, haystack = normalise(quote), normalise(source)
    if needle in haystack:
        return GroundingResult(True, 1.0, quote, "exact match")

    folded_needle, folded_haystack = _fold(quote), _fold(source)
    if folded_needle in folded_haystack:
        return GroundingResult(True, 0.97, quote, "matched after OCR folding")

    score, window = _best_window(folded_needle, folded_haystack)
    if score < threshold:
        return GroundingResult(
            False, score, window,
            reason=f"no matching text on the page (best {score:.0%})",
        )

    # Words can be damaged; the figures cannot be absent.
    quote_digits = digits_of(quote)
    if quote_digits and quote_digits not in digits_of(source):
        return GroundingResult(
            False, score, window,
            reason=f"the figure {quote_digits} does not appear in the source",
        )

    return GroundingResult(True, round(score, 3), window, "approximate match")


def _best_window(needle: str, haystack: str) -> tuple[float, str]:
    """Best similarity between `needle` and any same-length window of `haystack`.

    Stepped rather than exhaustive: a quarter-length stride finds the right
    neighbourhood, and the matcher tolerates the offset that remains. Comparing
    every offset of a long page for every candidate clause is far too slow for
    no measurable gain in accuracy.
    """
    if not needle or not haystack:
        return 0.0, ""
    if len(needle) >= len(haystack):
        return SequenceMatcher(None, needle, haystack).ratio(), haystack

    span = len(needle)
    stride = max(1, span // 4)
    best_score, best_window = 0.0, ""

    for start in range(0, len(haystack) - span + 1, stride):
        window = haystack[start : start + span]
        # Cheap prefilter: windows sharing no character run cannot win.
        matcher = SequenceMatcher(None, needle, window)
        if matcher.real_quick_ratio() < best_score:
            continue
        score = matcher.ratio()
        if score > best_score:
            best_score, best_window = score, window
            if best_score > 0.99:
                break

    return best_score, best_window


def find_in_page(quote: str, source: str) -> str | None:
    """Return the source's own wording for `quote`, if it can be located.

    Preferring the document's exact characters over the model's paraphrase keeps
    the evidence shown to a user faithful to their document.
    """
    result = check(quote, source)
    if not result.grounded:
        return None

    needle, haystack = normalise(quote), normalise(source)
    index = haystack.find(needle)
    if index >= 0:
        # Map back through the original casing and spacing.
        return _slice_original(source, index, len(needle))
    return result.matched_text or quote


def _slice_original(source: str, norm_start: int, norm_len: int) -> str:
    """Map an offset in normalised text back onto the original string."""
    original_index = 0
    normalised_index = 0
    start = None

    for original_index, char in enumerate(source):
        is_space = char.isspace()
        if is_space and (
            normalised_index == 0 or normalised_index and source[:original_index].strip() == ""
        ):
            continue

        if normalised_index == norm_start and start is None:
            start = original_index
        if normalised_index >= norm_start + norm_len:
            return source[start:original_index].strip()

        normalised_index += 1

    return source[start:].strip() if start is not None else source.strip()
