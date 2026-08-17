"""Boundaries on what this system is allowed to say.

The problem statement is explicit: the solution must function strictly as
decision support and must not provide medical diagnoses, clinical treatment
recommendations, or binding insurance advice. Those are not stylistic
preferences, a tool that drifts into clinical advice is dangerous, and one that
states a payout as a promise will be relied on and then contradicted by an
insurer.

Two things are enforced here. Every cost figure is framed as an estimate, and
model-written text is checked for clinical language before it reaches a user.
Deterministic output does not need scanning; it is written in this repository
and reviewed. Model output does, because it is not.
"""

from __future__ import annotations

import re

DISCLAIMER = (
    "Estimates are for guidance only. They are not a quote, not an approval, "
    "and not medical advice. Confirm all amounts with your insurer and the "
    "hospital insurance desk."
)

SHORT_DISCLAIMER = "Estimate only. Confirm with your insurer."

# Phrasings that would make an estimate read as a commitment.
_PROMISE_PATTERNS = [
    (re.compile(r"\byou will (?:be paid|receive|get)\b", re.I), "you would likely receive"),
    (re.compile(r"\bwill be (?:covered|reimbursed|approved)\b", re.I), "is likely to be covered"),
    (re.compile(r"\bguarantee[sd]?\b", re.I), "expect"),
    (re.compile(r"\bis covered\b", re.I), "appears to be covered"),
    (re.compile(r"\byour claim will\b", re.I), "your claim would likely"),
]

# Language that crosses from information into clinical direction.
_CLINICAL_PATTERNS = [
    re.compile(r"\byou should (?:take|have|undergo|get) (?:the|a|an|this)\b", re.I),
    re.compile(r"\bwe recommend (?:the|a|an|this) (?:treatment|procedure|surgery|drug|medication)\b", re.I),
    re.compile(r"\byou (?:have|are suffering from|are diagnosed with)\b", re.I),
    re.compile(r"\bdiagnos(?:is|ed|e) (?:is|as|with)\b", re.I),
    re.compile(r"\b(?:best|better|preferred) treatment (?:option|for you)\b", re.I),
    re.compile(r"\bdo not (?:take|have|undergo)\b", re.I),
    re.compile(r"\bthis (?:procedure|surgery|treatment) is (?:safe|unsafe|necessary)\b", re.I),
]


def soften_promises(text: str) -> str:
    """Rewrite commitment language into the estimate it actually is."""
    for pattern, replacement in _PROMISE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def contains_clinical_advice(text: str) -> bool:
    return any(pattern.search(text) for pattern in _CLINICAL_PATTERNS)


def sanitise(text: str, *, fallback: str = "") -> str:
    """Clean model-written text, or drop it if it strayed into clinical advice.

    Dropping is the right response rather than editing: text that recommends a
    treatment cannot be repaired into safe guidance by substituting words, and
    a partial rewrite would leave the intent intact while hiding the signal.
    """
    if not text:
        return text
    if contains_clinical_advice(text):
        return fallback
    return soften_promises(text)


def with_disclaimer(text: str) -> str:
    return f"{text}\n\n{SHORT_DISCLAIMER}" if text else SHORT_DISCLAIMER
