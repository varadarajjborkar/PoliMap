"""The IRDAI standard list of items an insurer will not reimburse.

Every Indian hospital bill carries lines that no health policy pays. Some are
genuinely the family's own cost, gloves and syringes and the attendant's meals.
Others should never have appeared as a separate line at all: the regulator has
ruled that they are already inside the room charge, or inside the procedure
charge, and billing them again is billing twice for one thing.

That second group is the one worth knowing about, and almost nobody does. A
family reading "Gown - Rs. 250" assumes it is a real cost they must pay because
their policy excludes it. It is not: the hospital has broken out something the
room rent already covers, and asking for it to be removed is a request the
billing desk is obliged to honour. This module exists so that a bill can be read
back to the person holding it with that distinction intact.

Four lists, from the IRDAI standard schedule of excluded and subsumed items
(circulated with the standardisation guidelines and carried into the master
circular of 29 May 2024):

  I    optional cover: not payable unless a rider was bought
  II   already inside the room charge
  III  already inside the procedure charge
  IV   already inside the cost of treatment

Matching is deliberately cautious. A wrong flag sends somebody to argue at a
billing counter over a charge that was correct, which costs them standing they
will need for the charges that were not, so a phrase must appear as whole words
and the guards below veto the readings that are merely lexical: an oxygen mask
is not the surgical mask of List III.
"""

from __future__ import annotations

import re
from enum import StrEnum


class ItemList(StrEnum):
    OPTIONAL = "optional"
    IN_ROOM = "in_room"
    IN_PROCEDURE = "in_procedure"
    IN_TREATMENT = "in_treatment"

    @property
    def label(self) -> str:
        return {
            ItemList.OPTIONAL: "Not covered by any health policy",
            ItemList.IN_ROOM: "Already inside the room charge",
            ItemList.IN_PROCEDURE: "Already inside the procedure charge",
            ItemList.IN_TREATMENT: "Already inside the cost of treatment",
        }[self]

    @property
    def is_subsumed(self) -> bool:
        """Whether the item should not be a separate line at all."""
        return self is not ItemList.OPTIONAL

    @property
    def ask(self) -> str:
        """What to say at the billing counter."""
        return {
            ItemList.OPTIONAL: (
                "This one is yours to pay. It is on the IRDAI list of items no "
                "health policy covers, so it belongs on your side of the bill "
                "rather than the insurer's."
            ),
            ItemList.IN_ROOM: (
                "Ask for this to be removed. The IRDAI list places it inside the "
                "room charge you are already paying, so billing it separately "
                "charges you twice for the same thing."
            ),
            ItemList.IN_PROCEDURE: (
                "Ask for this to be removed. The IRDAI list places it inside the "
                "procedure charge, so it should not appear as a line of its own."
            ),
            ItemList.IN_TREATMENT: (
                "Ask for this to be removed. The IRDAI list places it inside the "
                "cost of treatment, so it should not appear as a line of its own."
            ),
        }[self]


# Phrases, longest match wins. Written as they appear on bills rather than as
# the regulator words them: a bill says "ATTENDANT CHARGES", not "charges for
# the attendant of the patient".
_ITEMS: dict[ItemList, tuple[str, ...]] = {
    ItemList.OPTIONAL: (
        "baby food", "baby utility charges", "baby utility", "beauty services",
        "belts", "braces", "buds", "barber charges", "barber", "caps",
        "cold pack", "hot pack", "carry bags", "carry bag", "cradle charges",
        "comb", "cosmetics", "disposable razor", "razor", "eau de cologne",
        "email charges", "internet charges", "attendant food", "guest food",
        "visitor food", "foot cover", "gown", "leggings", "laundry charges",
        "laundry", "mineral water", "sanitary pad", "slippers",
        "telephone charges", "telephone", "tissue paper", "tooth paste",
        "toothpaste", "tooth brush", "toothbrush", "guest services",
        "television charges", "tv charges", "attendant charges", "attendant",
        "admission charges", "registration charges", "registration fee",
        "registration", "documentation charges", "administrative charges",
        "administration charges", "medical records charges", "medical records",
        "medico legal charges", "medico legal", "birth certificate charges",
        "certificate charges", "courier charges", "courier",
        "conveyance charges", "diabetic chart charges", "discharge procedure",
        "daily chart charges", "entrance pass", "visitors pass",
        "file opening charges", "file charges", "incidental expenses",
        "incidental charges", "patient identification band", "id band",
        "luxury tax", "hiv kit", "service charges", "surcharge",
        "night charges", "washing charges", "maintenance charges",
    ),
    ItemList.IN_ROOM: (
        "hand wash", "handwash", "shoe cover", "apron", "tourniquet",
        "torniquet", "bed pan", "bedpan", "urinal", "clean sheet",
        "linen charges", "bed sheet", "nebulisation kit",
    ),
    ItemList.IN_PROCEDURE: (
        "surgical blade", "harmonic scalpel", "surgical drill", "eye pad",
        "eye sheet", "camera cover", "dvd charges", "cd charges", "gauze soft",
        "gauze", "ward booking charges", "theatre booking charges",
        "microscope cover", "surgical drape", "drape", "mask",
        "sterile water", "surgical unit", "orthobundle", "gynaec bundle",
    ),
    ItemList.IN_TREATMENT: (
        "admission kit", "diabetic chart", "discharge summary charges",
        "arm sling", "thermometer", "cervical collar", "splint",
        "eyelet collar", "sling", "blood grouping", "cross matching",
        "antiseptic mouthwash", "mouthwash", "lozenges", "mouth paint",
        "vaccination charges", "alcohol swab", "scrub solution", "sterillium",
        "diaper",
    ),
}

# Readings that are lexical rather than real, as patterns over the normalised
# description. A mask that delivers oxygen is not the surgical mask of List III,
# "CAPS" on a pharmacy line is capsules rather than headwear, and a nursing
# attendant is care staff rather than the family member sleeping in the chair.
# Each of these was a wrong flag before it was a rule.
_VETOES: dict[str, tuple[str, ...]] = {
    "mask": (r"oxygen|nebuli|bipap|cpap|ventilat|venturi|nrbm",),
    "caps": (r"\d\s*(mg|ml|mcg|gm)\b", r"\b(tab|tabs|inj|syp|syrup|cap)\b"),
    "gauze": (r"\bdressing\b",),
    "attendant": (r"\bnurs",),
}

_PHRASES: list[tuple[str, ItemList]] = sorted(
    ((phrase, listing) for listing, phrases in _ITEMS.items() for phrase in phrases),
    key=lambda pair: len(pair[0]),
    reverse=True,
)

_WORD_SPLIT = re.compile(r"[^a-z0-9]+")


def normalise(description: str) -> str:
    """Bill descriptions arrive shouted, abbreviated and punctuated at random."""
    return " ".join(w for w in _WORD_SPLIT.split(description.lower()) if w)


def _contains(haystack: str, phrase: str) -> bool:
    """Whole-word containment, so "capsule" is not read as "caps"."""
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", haystack) is not None


def _vetoed(phrase: str, text: str) -> bool:
    """Whether a match is one of the readings that is lexical rather than real.

    Keyed on any veto whose word appears in the matched phrase, not on the
    phrase itself: "attendant charges" is the longer match and would otherwise
    step around the rule that spares a nursing attendant.
    """
    return any(
        re.search(pattern, text)
        for key, patterns in _VETOES.items()
        if _contains(phrase, key)
        for pattern in patterns
    )


def classify(description: str) -> tuple[str, ItemList] | None:
    """Return the phrase matched and the list it sits on, or None."""
    text = normalise(description)
    if not text:
        return None

    for phrase, listing in _PHRASES:
        if not _contains(text, phrase):
            continue
        if _vetoed(phrase, text):
            continue
        return phrase, listing
    return None
