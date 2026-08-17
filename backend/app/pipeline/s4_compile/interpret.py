"""Understand what someone typed, without letting them drive the engine.

The clarification questions used to offer fixed choices and a box that accepted
digits. Both assume the user's situation is one the form anticipated. Often it
is not: they know the answer in words rather than numbers ("about five lakh",
"one percent of my cover per day"), or their answer is none of the options
offered, or the figure on their document is written in a form the box rejects.

So free text is accepted. What it is *not* allowed to do is steer the pipeline.
Text is interpreted into the fields this system already has, and only those. The
alternative, letting an answer invent fields, produces the failure the design
has to survive: someone types a near-miss of a real field name, "name3" for
"name", and a system that creates whatever it is handed ends up holding both,
with one of them wrong and no way to tell which.

Two rules follow from that.

**Deterministic first.** Indian amounts are written in a small number of
recognisable ways, and a rule that reads "5 lakh" costs nothing and cannot
hallucinate. The model is asked only about text the rules could not settle.

**Ambiguity is a question, not a guess.** When an interpretation is uncertain,
or when one answer appears to set the same field twice, the result is a
confirmation with the readings offered as choices. Guessing silently is how the
near-miss becomes a wrong number nobody notices.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, Field

from app.agents.base import LLMUnavailable
from app.agents.registry import registry
from app.core.config import ModelRole
from app.core.logging import get_logger
from app.schemas.money import round_inr

log = get_logger(__name__)

# Indian scale words, and the plain ones people mix with them.
_SCALES: dict[str, Decimal] = {
    "k": Decimal(1_000),
    "thousand": Decimal(1_000),
    "hazaar": Decimal(1_000),
    "hazar": Decimal(1_000),
    "l": Decimal(100_000),
    "lac": Decimal(100_000),
    "lacs": Decimal(100_000),
    "lakh": Decimal(100_000),
    "lakhs": Decimal(100_000),
    "lakha": Decimal(100_000),
    "cr": Decimal(10_000_000),
    "crore": Decimal(10_000_000),
    "crores": Decimal(10_000_000),
    "million": Decimal(1_000_000),
    "mn": Decimal(1_000_000),
}

_WORD_NUMBERS: dict[str, Decimal] = {
    "half": Decimal("0.5"), "one": Decimal(1), "two": Decimal(2),
    "three": Decimal(3), "four": Decimal(4), "five": Decimal(5),
    "six": Decimal(6), "seven": Decimal(7), "eight": Decimal(8),
    "nine": Decimal(9), "ten": Decimal(10), "eleven": Decimal(11),
    "twelve": Decimal(12), "fifteen": Decimal(15), "twenty": Decimal(20),
    "twentyfive": Decimal(25), "fifty": Decimal(50), "hundred": Decimal(100),
}

# People answer "I don't know" and "we have no idea" as often as "none". Both
# are answers worth recording: "no limit" is a fact about the policy, and "I
# don't know" is a reason to stop asking and carry on with what we have.
#
# Filler is stripped and the remainder matched exactly, rather than growing one
# regex to cover every phrasing. An exact match on a short list is the part that
# matters: a loose pattern that also swallows "i know it is 5 lakh" would record
# "no answer" over a perfectly good one.
_FILLER = {
    "i", "we", "it", "its", "it's", "there", "is", "are", "am", "was",
    "have", "has", "had", "do", "does", "did", "really", "honestly",
    "sorry", "actually", "just", "the", "my", "our", "policy", "sure",
}

_NO_ANSWER = {
    "no", "none", "nil", "nothing", "na", "n/a", "not applicable",
    "no limit", "nolimit", "unlimited", "no cap", "not sure", "unsure",
    "no idea", "dont know", "do not know", "not known", "no clue",
    "cant say", "can not say", "not mentioned", "not stated", "blank",
}


class Reading(BaseModel):
    """One way the text could be understood, and how sure we are."""

    value: Decimal | None = None
    is_none: bool = False
    """The user said there is no such limit, which is an answer, not a blank."""

    restated: str = ""
    """What we think they meant, in our own words, for them to confirm."""

    confidence: float = 0.0
    source: str = "rules"


class Interpretation(BaseModel):
    """What we made of an answer, and whether we should check before using it."""

    readings: list[Reading] = Field(default_factory=list)
    needs_confirmation: bool = False
    reason: str = ""

    @property
    def best(self) -> Reading | None:
        return self.readings[0] if self.readings else None


def parse_amount(text: str) -> Decimal | None:
    """Read a rupee figure written the way people actually write it.

    Handles "5 lakh", "5L", "5,00,000", "Rs. 5 lakhs", "50k", "2.5 lakh",
    "five lakh". Returns None rather than a guess when nothing is recognisable,
    because a wrong figure here becomes a wrong figure in every estimate after.
    """
    if not text:
        return None

    cleaned = (
        text.lower()
        .replace("₹", " ")
        .replace("rs.", " ").replace("rs", " ").replace("inr", " ")
        .replace("/-", " ")
        .replace("per day", " ").replace("a day", " ").replace("daily", " ")
        .replace("about", " ").replace("around", " ").replace("approx", " ")
        .replace(",", "")
        .strip()
    )
    if not cleaned:
        return None

    # "5 lakh", "5lakh", "2.5 lakhs", "50k"
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*([a-z]+)?", cleaned
    )
    word_match = re.search(
        r"\b(" + "|".join(_WORD_NUMBERS) + r")\s*([a-z]+)?", cleaned
    )

    number: Decimal | None = None
    scale_word = ""

    if match:
        try:
            number = Decimal(match.group(1))
        except InvalidOperation:
            number = None
        scale_word = (match.group(2) or "").strip()
    elif word_match:
        # A spelled-out number is only an amount when it is doing the work of
        # one: followed by a scale word, or standing as the whole answer.
        # Without this, "the blue one" reads as one rupee, which is the exact
        # class of silent wrong figure this function exists to avoid.
        scale_word = (word_match.group(2) or "").strip()
        standalone = cleaned.split() == [word_match.group(1)]
        if scale_word in _SCALES or standalone:
            number = _WORD_NUMBERS[word_match.group(1)]
        else:
            return None

    if number is None:
        return None

    if scale_word in _SCALES:
        number *= _SCALES[scale_word]
    elif scale_word and scale_word not in ("rupees", "rupee", "only", "per", "day"):
        # A trailing word we do not recognise means the text is doing something
        # the rules do not cover. Better to hand it on than to drop the word and
        # keep the number.
        return None

    if number <= 0:
        return None
    return round_inr(number)


def parse_percent(text: str) -> Decimal | None:
    """Read a percentage, including "one percent of my cover"."""
    if not text:
        return None
    lowered = text.lower()

    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|per\s*cent|percent|pc\b)", lowered)
    if match:
        try:
            return Decimal(match.group(1))
        except InvalidOperation:
            return None

    word = re.search(
        r"\b(" + "|".join(_WORD_NUMBERS) + r")\s*(?:%|per\s*cent|percent)", lowered
    )
    return _WORD_NUMBERS[word.group(1)] if word else None


def says_nothing_applies(text: str) -> bool:
    """Whether the user said there is no such limit, or that they do not know.

    Both are answers worth recording. "No limit" is a fact about the policy;
    "I don't know" is a reason to stop asking and move on with what we have.
    """
    cleaned = re.sub(r"[.!?,]", " ", (text or "").lower())
    cleaned = cleaned.replace("'", "").replace("’", "")
    words = [w for w in cleaned.split() if w]

    # Drop leading filler only. Stripping it from anywhere would turn
    # "i know it is 5 lakh" into "know 5 lakh" and lose the figure.
    while words and words[0] in _FILLER:
        words.pop(0)

    return " ".join(words) in _NO_ANSWER


# --- the model fallback -----------------------------------------------------


class _ModelReading(BaseModel):
    understood: bool = Field(
        description="Whether the answer states a value for the question asked"
    )
    amount_inr: str = Field(
        default="",
        description="The rupee figure, digits only, or empty if not a rupee figure",
    )
    percent: str = Field(
        default="",
        description="The percentage, digits only, or empty if not a percentage",
    )
    means_no_limit: bool = Field(
        default=False, description="Whether the answer says there is no such limit"
    )
    restated: str = Field(
        description="What the answer means, in one short plain sentence"
    )
    ambiguous: bool = Field(
        default=False,
        description=(
            "Whether the answer could reasonably mean more than one thing, or "
            "appears to give two different values for the same question"
        ),
    )


_SYSTEM = (
    "You interpret short answers that people give about their health insurance. "
    "You map an answer onto the single field that was asked about and nothing "
    "else. You never invent a field, never carry over a value from a different "
    "question, and never fill in what a typical policy would say. If an answer "
    "is unclear, or gives two different values, you mark it ambiguous rather "
    "than choosing one."
)

_PROMPT = """A user was asked this question about their health insurance:

  {question}

They answered:

  {answer}

Interpret their answer as a value for that question only.

- If they gave a rupee amount, put digits only in "amount_inr". Indian scale
  words are common: "5 lakh" is 500000, "50k" is 50000, "1 crore" is 10000000.
- If they gave a percentage, put digits only in "percent".
- If they said there is no such limit, set "means_no_limit".
- If the answer does not state a value for this question at all, set
  "understood" to false. Do not guess.
- If the answer gives two different values, or could mean more than one thing,
  set "ambiguous" to true.
- "restated" is one short sentence a non-expert would recognise as what they
  meant. It is shown back to them for confirmation.
"""


def interpret(question: str, answer: str, *, expects: str = "amount") -> Interpretation:
    """Turn a free-text answer into a value, or into a question to confirm.

    `expects` is "amount" or "percent", and comes from the field being asked
    about rather than from the answer. An answer is never allowed to decide
    which field it lands in; that is what keeps a typed near-miss from creating
    a second, wrong field alongside the real one.
    """
    text = (answer or "").strip()
    if not text:
        return Interpretation(reason="Nothing was entered.")

    if says_nothing_applies(text):
        return Interpretation(readings=[Reading(
            is_none=True,
            restated="You have told us this does not apply.",
            confidence=1.0,
        )])

    # Rules first. They cost nothing, cannot hallucinate, and cover the forms
    # people actually write amounts in.
    if expects == "percent":
        if (pct := parse_percent(text)) is not None:
            return Interpretation(readings=[Reading(
                value=pct, restated=f"{pct:g}%", confidence=0.95,
            )])
    else:
        if (amount := parse_amount(text)) is not None:
            from app.schemas.money import format_inr
            return Interpretation(readings=[Reading(
                value=amount, restated=format_inr(amount), confidence=0.95,
            )])

    return _ask_a_model(question, text, expects)


def _ask_a_model(question: str, text: str, expects: str) -> Interpretation:
    try:
        reading = registry.complete_structured(
            ModelRole.NARRATE,
            prompt=_PROMPT.format(question=question, answer=text),
            schema=_ModelReading,
            system=_SYSTEM,
            temperature=0.0,
        )
    except LLMUnavailable:
        # Without a model this is simply not understood, which is an honest
        # outcome. Inventing a number from unparseable text would be worse
        # than admitting the rules did not cover it.
        return Interpretation(
            reason=(
                "We could not read that as an amount. Try writing it as a "
                "number, for example 500000 or 5 lakh."
            )
        )

    if not reading.understood:
        return Interpretation(
            reason=(
                "That did not look like an answer to this question. You can "
                "skip it if you are not sure."
            )
        )

    if reading.means_no_limit:
        return Interpretation(readings=[Reading(
            is_none=True, restated=reading.restated, confidence=0.8, source="model",
        )])

    raw = reading.percent if expects == "percent" else reading.amount_inr
    try:
        value = Decimal(raw.replace(",", "").strip()) if raw.strip() else None
    except InvalidOperation:
        value = None

    if value is None or value <= 0:
        return Interpretation(
            reason="We could not turn that into a figure. Try writing the number."
        )

    if expects != "percent":
        value = round_inr(value)

    # Anything from the model is confirmed before it is used. The point of the
    # free-text box is to accept what a person meant, not to let a paraphrase
    # of it become a settled number without them seeing it.
    return Interpretation(
        readings=[Reading(
            value=value, restated=reading.restated, confidence=0.6, source="model",
        )],
        needs_confirmation=True,
        reason=(
            "Two readings are possible here, so please confirm."
            if reading.ambiguous else
            "Please confirm we understood you."
        ),
    )
