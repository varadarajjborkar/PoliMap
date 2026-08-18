"""Placing a bill line under the expense head that decides how it settles.

A hospital bill is a list of things bought. A policy is a set of rules about
categories: proportionate deduction touches some heads and not others, sub-limits
cap particular heads, and consumables are excluded by default. Nothing can be
checked until each line has been placed, so this is the join between the two.

Two signals, in order of strength. Indian bills are laid out in sections, so a
line under a "PHARMACY CHARGES" banner is pharmacy whatever it is called, and a
running section beats a keyword. Failing that, the description's own words.

A line that neither signal places is left unplaced rather than guessed. The
guess would be invisible: it would move a few thousand rupees into a head that
carries a sub-limit or a deduction it should never have met, and the reader
would have no way of knowing that the number they are being shown rests on it.
Unplaced lines are reported as unplaced, with their total.
"""

from __future__ import annotations

import re

from app.schemas.policy import ExpenseHead

# Ordered: the first head whose pattern matches wins, so the specific sits above
# the general. "ICU nursing" is intensive care, not nursing; "OT consumables"
# is theatre, not consumables.
_HEAD_PATTERNS: list[tuple[ExpenseHead, str]] = [
    (ExpenseHead.ICU_CHARGES,
     r"\b(icu|iccu|nicu|picu|hdu|itu|intensive care|critical care)s?\b"),
    (ExpenseHead.AMBULANCE, r"\bambulance\b"),
    (ExpenseHead.IMPLANTS,
     r"\b(implant|stent|prosthes|prosthetic|graft|mesh|pacemaker|"
     r"bone cement|iol|intraocular|screw|nail plate|k wire|coil)s?\b"),
    # Blood as a test rather than as a bag of it. Grouping and cross-matching
    # sit on the IRDAI list too, but they are investigations first.
    (ExpenseHead.INVESTIGATIONS,
     r"\bblood\s+(group|grouping|sugar|urea|culture|count|gas|test|cbc)"),
    (ExpenseHead.BLOOD,
     r"\b(blood|plasma|platelet|prbc|frozen plasma|transfusion)s?\b"),
    (ExpenseHead.OXYGEN, r"\b(oxygen|o2)s?\b"),
    (ExpenseHead.PHYSIOTHERAPY, r"\b(physio|physiotherapy|rehab)s?\b"),
    (ExpenseHead.ANAESTHETIST_FEE, r"\b(anaesth|anesth)"),
    (ExpenseHead.SURGEON_FEE,
     r"\b(surgeon|surgery charge|operative charge|procedure charge)s?\b"),
    (ExpenseHead.OT_CHARGES,
     r"\b(ot|o\.t|operation theatre|operating theatre|theatre|cath lab|"
     r"endoscopy suite)s?\b"),
    (ExpenseHead.ROOM_RENT,
     r"\b(room rent|room charge|bed charge|accommodation|ward charge|"
     r"bed rent|room tariff)s?\b"),
    (ExpenseHead.NURSING, r"\b(nursing|nurse)s?\b"),
    (ExpenseHead.DOCTOR_VISIT,
     r"\b(consultant|consultation|doctor visit|physician|rmo|visiting|"
     r"visit charge|rounds)s?\b"),
    (ExpenseHead.INVESTIGATIONS,
     r"\b(lab|laborator|patholog|radiolog|x ray|xray|ct|mri|usg|ultrasound|"
     r"ecg|ekg|echo\w*|angiogram|angiography|biopsy|culture|scan|profile|"
     r"haemogram|hemogram|cbc|creatinine|troponin|investigation|diagnostic|"
     r"test|report charge|histopath|doppler|tmt|holter)s?\b"),
    (ExpenseHead.PHARMACY,
     r"\b(pharmac|medicine|medication|drug|inj|injection|tab|tabs|cap|caps|"
     r"capsule|syrup|syp|iv fluid|infusion|ointment|nebulis|antibiotic)s?\b"),
    (ExpenseHead.CONSUMABLES,
     r"\b(consumable|disposable|syringe|cannula|catheter|glove|cotton|"
     r"bandage|dressing|surgical item|needle|tube|drain|kit)s?\b"),
    (ExpenseHead.NON_MEDICAL,
     r"\b(registration|admission charge|administrat|medical record|attendant|"
     r"telephone|television|tv charge|laundry|incidental|documentation|"
     r"service charge|surcharge|courier|certificate)s?\b"),
]

_COMPILED: list[tuple[ExpenseHead, re.Pattern[str]]] = [
    (head, re.compile(pattern, re.IGNORECASE)) for head, pattern in _HEAD_PATTERNS
]

# A banner line naming the section that follows. Distinguished from an item by
# carrying no amount, which the reader checks before calling this.
_SECTION_PATTERNS: list[tuple[ExpenseHead, str]] = [
    (ExpenseHead.ICU_CHARGES, r"\b(icu|intensive care|critical care)s?\b"),
    (ExpenseHead.PHARMACY, r"\b(pharmacy|medicine|drug|medication)s?\b"),
    (ExpenseHead.INVESTIGATIONS,
     r"\b(investigation|laborator|lab|diagnostic|radiolog|patholog|test)s?\b"),
    (ExpenseHead.CONSUMABLES, r"\b(consumable|disposable|surgical item)s?\b"),
    (ExpenseHead.IMPLANTS, r"\b(implant|device)s?\b"),
    (ExpenseHead.OT_CHARGES, r"\b(operation theatre|theatre|ot)s?\b"),
    (ExpenseHead.ROOM_RENT, r"\b(room|bed|accommodation|ward)s?\b"),
    (ExpenseHead.NURSING, r"\bnursing\b"),
    (ExpenseHead.DOCTOR_VISIT, r"\b(professional|consultant|doctor|visit)s?\b"),
    (ExpenseHead.SURGEON_FEE, r"\b(surgical|surgery|surgeon|procedure)s?\b"),
    (ExpenseHead.NON_MEDICAL,
     r"\b(non medical|other charge|miscellaneous|misc|administrat)s?\b"),
]

_COMPILED_SECTIONS: list[tuple[ExpenseHead, re.Pattern[str]]] = [
    (head, re.compile(pattern, re.IGNORECASE)) for head, pattern in _SECTION_PATTERNS
]

_TIDY = re.compile(r"[^a-z0-9]+")


def _flatten(text: str) -> str:
    return " ".join(w for w in _TIDY.split(text.lower()) if w)


def head_of(description: str) -> ExpenseHead | None:
    """The head this line belongs under, or None if its words do not say."""
    text = _flatten(description)
    if not text:
        return None
    for head, pattern in _COMPILED:
        if pattern.search(text):
            return head
    return None


def section_head(banner: str) -> ExpenseHead | None:
    """The head a section banner opens, or None if the line is not a banner.

    Looser than `head_of` on purpose: a banner reading "PHARMACY" is placing
    everything beneath it, so a single word is enough, where the same word
    inside an item description would not be.
    """
    text = _flatten(banner)
    if not text or len(text) > 60:
        return None
    for head, pattern in _COMPILED_SECTIONS:
        if pattern.search(text):
            return head
    return None
