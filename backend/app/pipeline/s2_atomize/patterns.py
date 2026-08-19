"""Parsing of Indian policy notation.

Indian insurance documents write the same quantity many ways. One corpus can
contain "Rs. 5,00,000/-", "INR 5,00,000", "₹5,00,000", "Rs. 5.00 Lakhs" and
"Rupees Five Lakh Only" for the identical figure, and a room limit may be a
rupee amount, a percentage of sum insured, both at once ("1% subject to a
maximum of Rs. 5,000"), or a room category carrying no number at all.

Parsing this deterministically matters beyond tidiness. These rules are the
system's floor: they run with no model, no key and no network, and they are the
only part of extraction whose behaviour is fully predictable. The language model
widens recall on unusual phrasings; it does not replace this.

Lakh and crore are handled natively rather than converted at the edges, because
"5.5 Lakhs" is a genuinely different token from "550000" and OCR sees the former.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

LAKH = Decimal(100000)
CRORE = Decimal(10000000)

# Currency markers that may precede an amount.
_CURRENCY = r"(?:₹|Rs\.?|INR|Rupees)"

# A grouped or plain number: 5,00,000 or 500000 or 5.00
_NUMBER = r"\d[\d,]*(?:\.\d+)?"

# Trailing scale words.
_SCALE = r"(?:lakhs?|lacs?|crores?|cr\b|L\b)"

AMOUNT_RE = re.compile(
    rf"(?P<currency>{_CURRENCY})?\s*"
    rf"(?P<number>{_NUMBER})\s*"
    rf"(?P<scale>{_SCALE})?\s*"
    rf"(?P<trailer>/-|/=)?",
    re.IGNORECASE,
)

PERCENT_RE = re.compile(r"(?P<pct>\d+(?:\.\d+)?)\s*(?:%|per\s*cent|percent)", re.IGNORECASE)

PCT_OF_SI_RE = re.compile(
    r"(?P<pct>\d+(?:\.\d+)?)\s*(?:%|per\s*cent|percent)\s*"
    r"(?:of\s+(?:the\s+)?)?(?:sum\s+insured|SI|sum\s+assured)",
    re.IGNORECASE,
)

_WORD_VALUES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}
_WORD_SCALES = {"hundred": 100, "thousand": 1000, "lakh": 100000, "lakhs": 100000,
                "crore": 10000000, "crores": 10000000}

WORDS_AMOUNT_RE = re.compile(
    r"Rupees\s+(?P<words>[A-Za-z\s]+?)\s*(?:Only|/-|$)", re.IGNORECASE
)


def _amount_from_match(match: re.Match[str]) -> Decimal | None:
    """Interpret one regex match, or reject it as not being money."""
    number = match.group("number")
    if not number:
        return None
    try:
        value = Decimal(number.replace(",", ""))
    except InvalidOperation:
        return None

    scale = (match.group("scale") or "").lower()
    if scale.startswith(("lakh", "lac")) or scale == "l":
        value *= LAKH
    elif scale.startswith(("crore", "cr")):
        value *= CRORE

    # A bare number with no currency marker, no scale and no trailer is too
    # weak to treat as money; it is as likely a clause number or a date part.
    if not match.group("currency") and not scale and not match.group("trailer"):
        return None

    return value


def parse_amount(text: str) -> Decimal | None:
    """Read the first genuine rupee figure in `text`.

    Scans every candidate rather than stopping at the first regex hit. Policy
    limits routinely lead with a percentage, "1% of Sum Insured per day,
    subject to a maximum of Rs. 5,000", and the leading "1" matches the number
    pattern while failing the currency test. Bailing out there loses the actual
    cap and silently reports the policy as uncapped in rupees, which is exactly
    the sort of confident wrong answer this parser exists to prevent.
    """
    if not text:
        return None

    if (spelled := parse_amount_in_words(text)) is not None:
        return spelled

    for match in AMOUNT_RE.finditer(text):
        value = _amount_from_match(match)
        if value is not None:
            return value
    return None


def parse_amount_in_words(text: str) -> Decimal | None:
    """Read "Rupees Five Lakh Only" style figures."""
    match = WORDS_AMOUNT_RE.search(text)
    if not match:
        return None

    total = Decimal(0)
    current = Decimal(0)
    seen = False

    for token in match.group("words").lower().split():
        if token in _WORD_VALUES:
            current += _WORD_VALUES[token]
            seen = True
        elif token in _WORD_SCALES:
            scale = Decimal(_WORD_SCALES[token])
            if scale >= LAKH:
                total += (current or 1) * scale
                current = Decimal(0)
            else:
                current = (current or 1) * scale
            seen = True
        elif token in ("and", "only", "rupees"):
            continue
        else:
            return None if not seen else None

    return (total + current) if seen else None


def parse_percent(text: str) -> Decimal | None:
    match = PERCENT_RE.search(text)
    return Decimal(match.group("pct")) if match else None


def parse_pct_of_sum_insured(text: str) -> Decimal | None:
    """Percentage explicitly tied to the sum insured, e.g. "1% of Sum Insured"."""
    match = PCT_OF_SI_RE.search(text)
    return Decimal(match.group("pct")) if match else None


def all_amounts(text: str) -> list[Decimal]:
    """Every rupee figure in `text`, in order of appearance."""
    return [
        value
        for match in AMOUNT_RE.finditer(text)
        if (value := _amount_from_match(match)) is not None
    ]


MAXIMUM_RE = re.compile(
    # "subject to a maximum of", "max.", "maximum of"
    r"(?:subject\s+to\s+(?:a\s+)?)?max(?:imum)?\.?\s+(?:of\s+)?|"
    # "capped at", "subject to a cap of"
    r"(?:subject\s+to\s+a\s+)?cap(?:ped)?\s+(?:at|of|to)\s+|"
    # "not exceeding", "not more than", "limited to", "restricted to"
    r"(?:but\s+)?not\s+(?:exceeding|more\s+than)\s+|"
    r"(?:limited|restricted)\s+to\s+|"
    # "up to", "up to a maximum of"
    r"up\s?to\s+(?:a\s+max\w*\s+of\s+)?",
    re.IGNORECASE,
)

WHICHEVER_LOWER_RE = re.compile(
    r"whichever\s+is\s+(?:lower|less|lesser|the\s+lower)|"
    r"whichever\s+is\s+(?:higher|more|greater)|"
    r"lower\s+of\s+the\s+two",
    re.IGNORECASE,
)
"""Both directions, because recognising that two figures were written as one
term is what matters here. Which of them binds is decided by the compiler from
the figures themselves, not from the wording."""


def has_max_qualifier(text: str) -> bool:
    """Whether `text` ties a second figure to the first as its ceiling.

    The test for "these two numbers are one term". Two figures with no such
    wording between them are two terms, and merging them would invent a limit
    the document does not state.
    """
    if not text:
        return False
    return bool(MAXIMUM_RE.search(text) or WHICHEVER_LOWER_RE.search(text))


def parse_capped_amount(text: str) -> Decimal | None:
    """The rupee ceiling in a "percentage, subject to a maximum of X" clause.

    Anchored on the words that introduce the ceiling rather than just taking the
    last figure, because a limit line often ends with an unrelated number, a
    per-day qualifier or a clause reference, and taking the last one gets it
    wrong in a way that is hard to notice.
    """
    match = MAXIMUM_RE.search(text)
    if match:
        after = parse_amount(text[match.end():])
        if after is not None:
            return after
    return parse_amount(text)


ROOM_CATEGORY_PATTERNS: list[tuple[str, str]] = [
    # Ordered most specific first: "single private a/c room" must not be
    # captured by the looser "private room" pattern.
    (r"general\s+ward|shared\s+ward|multi[- ]?bed", "general_ward"),
    (r"twin[- ]?shar\w*|two[- ]?bed|double\s+shar\w*|semi[- ]?private", "twin_sharing"),
    (r"single\s+(?:private\s+)?(?:a/?c\s+)?room|single\s+occupancy|"
     r"private\s+(?:a/?c\s+)?room", "single_private"),
    (r"deluxe\s+room|deluxe", "deluxe"),
    (r"suite|super\s+deluxe", "suite"),
]

_COMPILED_ROOM = [(re.compile(p, re.IGNORECASE), v) for p, v in ROOM_CATEGORY_PATTERNS]


def parse_room_category(text: str) -> str | None:
    """Identify a room category named in free text."""
    for pattern, value in _COMPILED_ROOM:
        if pattern.search(text):
            return value
    return None


NO_LIMIT_RE = re.compile(
    r"no\s+(?:sub[- ]?)?limit|not\s+applicable|no\s+capping|"
    r"any\s+room\s+categor|up\s+to\s+sum\s+insured|no\s+separate\s+sub[- ]?limit|"
    r"\bnil\b",
    re.IGNORECASE,
)


def states_no_limit(text: str) -> bool:
    return bool(NO_LIMIT_RE.search(text))


MONTHS_RE = re.compile(
    r"(?P<n>\d{1,3})\s*(?:months?|mths?)|"
    r"(?P<y>\d{1,2})\s*(?:years?|yrs?)",
    re.IGNORECASE,
)


def parse_months(text: str) -> int | None:
    """Read a duration in months, converting years where written that way."""
    match = MONTHS_RE.search(text)
    if not match:
        return None
    if match.group("n"):
        return int(match.group("n"))
    return int(match.group("y")) * 12


DAYS_RE = re.compile(r"(?P<n>\d{1,4})\s*days?", re.IGNORECASE)

_MONTH_NAMES = {
    name: number
    for number, names in enumerate(
        [
            ("jan", "january"), ("feb", "february"), ("mar", "march"),
            ("apr", "april"), ("may",), ("jun", "june"),
            ("jul", "july"), ("aug", "august"), ("sep", "sept", "september"),
            ("oct", "october"), ("nov", "november"), ("dec", "december"),
        ],
        start=1,
    )
    for name in names
}

# Day first, because that is how a policy schedule in India writes a date.
# `01/02/2026` on one of these is the first of February, and reading it the
# other way would move a policy's start by eleven months.
_NUMERIC_DATE = re.compile(
    r"\b(?P<d>\d{1,2})[/.-](?P<m>\d{1,2})[/.-](?P<y>\d{4}|\d{2})\b"
)
_ISO_DATE = re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})\b")
_WRITTEN_DATE = re.compile(
    r"\b(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?P<mon>[A-Za-z]{3,9})\.?,?\s+(?P<y>\d{4})\b"
)


def parse_date(text: str) -> date | None:
    """Read the first date in a line, tolerating the several ways one is written.

    A wrong date here is worse than none: policy start decides whether a
    waiting period has expired, and a year read as `26` instead of `2026` would
    make every waiting period look long since served. So the year is taken as
    written where it is four digits, and only a two-digit year is assumed to be
    this century.
    """
    iso = _ISO_DATE.search(text)
    if iso:
        return _safe_date(int(iso["y"]), int(iso["m"]), int(iso["d"]))

    written = _WRITTEN_DATE.search(text)
    if written:
        month = _MONTH_NAMES.get(written["mon"].lower())
        if month:
            return _safe_date(int(written["y"]), month, int(written["d"]))

    numeric = _NUMERIC_DATE.search(text)
    if numeric:
        year = int(numeric["y"])
        if year < 100:
            year += 2000
        return _safe_date(year, int(numeric["m"]), int(numeric["d"]))
    return None


def all_dates(text: str) -> list[date]:
    """Every date in a line, left to right.

    A policy period is one line holding two of them: "From 00:00 hrs on
    01/02/2026 to 23:59 hrs on 31/01/2027". Reading only the first would give a
    start with no end.
    """
    found: list[tuple[int, date]] = []
    seen: set[date] = set()
    for pattern in (_ISO_DATE, _WRITTEN_DATE, _NUMERIC_DATE):
        for match in pattern.finditer(text):
            parsed = parse_date(match.group(0))
            if parsed is not None and parsed not in seen:
                seen.add(parsed)
                found.append((match.start(), parsed))
    return [parsed for _, parsed in sorted(found)]


def _safe_date(year: int, month: int, day: int) -> date | None:
    """A date, or nothing. `31/02` is a misread, not a date to be salvaged."""
    if not 1900 <= year <= 2100:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_days(text: str) -> int | None:
    match = DAYS_RE.search(text)
    return int(match.group("n")) if match else None


# "for Insured Persons aged 61 years and above", "applicable above 60 years of
# age", "where the insured is 65 or older". A co-payment written this way falls
# on one member of a household and not the rest, and read without the band it
# takes a fifth off a child's claim.
AGE_BAND_RE = re.compile(
    r"(?:aged?|age\s+of|over|above|beyond)\s*(?P<n>\d{2})\s*(?:years?|yrs?)?"
    r"\s*(?:of\s+age\s*)?(?:and|or)?\s*(?:above|over|older|more|\+)?"
    r"|"
    r"(?P<m>\d{2})\s*(?:years?|yrs?)\s*(?:of\s+age\s*)?(?:and|or)\s*(?:above|over|older)",
    re.IGNORECASE,
)

MIN_AGE_BAND = 40
"""Below this the number is not an age band. A co-payment row mentioning "20%"
and "18" is not describing eighteen-year-olds."""


def parse_age_band(text: str) -> int | None:
    """The age at or above which something applies, if the text states one."""
    for match in AGE_BAND_RE.finditer(text):
        raw = match.group("n") or match.group("m")
        if raw is None:
            continue
        # Only count a bare "above 60" if the sentence is talking about age at
        # all; "above 60%" is a share, not a birthday.
        tail = text[match.end(): match.end() + 2]
        if tail.strip().startswith("%"):
            continue
        age = int(raw)
        if MIN_AGE_BAND <= age <= 99:
            return age
    return None


PER_DAY_RE = re.compile(r"per\s*day|/\s*day|daily|per\s+diem", re.IGNORECASE)


def is_per_day(text: str) -> bool:
    return bool(PER_DAY_RE.search(text))


MAX_PLAUSIBLE_ROOM_RATE = Decimal(200000)
"""Above this a figure on a room-rent line is something else: an annual cap, a
sum insured, a policy number that survived OCR as digits."""


def read_room_limit(text: str) -> dict[str, Any] | None:
    """Interpret a room or ICU limit in any of the forms policies use.

    One reader for both extractors. The rules and the model used to interpret
    the same sentence in two different places, and the model's copy did not
    know that a percentage and the ceiling attached to it are one term, so it
    reported the two halves as rival answers and the verification loop settled
    a contradiction that did not exist.

    "1% of Sum Insured per day, subject to a maximum of Rs. 5,000" is a single
    entitlement: whichever of the two binds lower on this policy's own sum
    insured. It stays one clause carrying both figures, and stays that way
    until the compiler resolves it.
    """
    if not text:
        return None
    if states_no_limit(text):
        return {"basis": "no_limit"}

    pct = parse_pct_of_sum_insured(text)
    # Anchored on the words that introduce a ceiling rather than on whichever
    # figure comes last, because a limit line often ends with a clause
    # reference or a per-day qualifier carrying digits of its own.
    amount = parse_capped_amount(text) if pct is not None else parse_amount(text)
    category = parse_room_category(text)

    if pct is not None and amount is not None and has_max_qualifier(text):
        return {
            "basis": "pct_with_max",
            "pct_of_si": str(pct),
            "amount_inr": str(amount),
            "per_day": is_per_day(text),
        }
    if pct is not None:
        return {"basis": "pct_of_si", "pct_of_si": str(pct)}
    if amount is not None and amount <= MAX_PLAUSIBLE_ROOM_RATE:
        return {"basis": "flat", "amount_inr": str(amount), "per_day": is_per_day(text)}
    if category is not None:
        return {"basis": "category", "category": category}
    return None


def normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
