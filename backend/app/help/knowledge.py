"""Loading what the help desk knows, and deciding what is being asked.

The answers themselves are in `knowledge.yaml`. This module is only the part
that is logic: reading that file once, and scoring a question against it.

Keeping the two apart is what makes the knowledge base editable. Every answer
used to be a Python literal several screens long, which meant that correcting a
sentence was a code change, and that the file holding the matching was mostly
not matching. Now a person can read every answer the help desk is capable of
giving in one sitting, and change one without being able to break anything.

The file is read with `safe_load`, which constructs nothing but the plain data
types. That matters more than it looks: YAML's full loader will instantiate
arbitrary Python objects named in a document, and a knowledge base is exactly
the kind of file that gets edited casually and shipped without much thought.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

KNOWLEDGE_FILE = Path(__file__).with_name("knowledge.yaml")


@dataclass(frozen=True)
class Answer:
    """One thing the help desk can say, and how to tell it is being asked."""

    key: str
    question: str
    """The question as somebody would actually ask it, for the suggestion chips."""
    body: str
    triggers: tuple[str, ...]
    """Words and phrases that mean this is being asked."""
    goes_to: str = ""
    """Where in the app this is about, if anywhere: a step id."""


@dataclass(frozen=True)
class _Base:
    answers: tuple[Answer, ...]
    by_key: dict[str, Answer]
    suggested: dict[str, tuple[str, ...]]
    default_suggestions: tuple[str, ...]


@lru_cache(maxsize=1)
def _base() -> _Base:
    raw = yaml.safe_load(KNOWLEDGE_FILE.read_text(encoding="utf-8"))

    answers = tuple(
        Answer(
            key=entry["key"],
            question=entry["question"],
            body=entry["body"].strip(),
            triggers=tuple(entry.get("triggers", ())),
            goes_to=entry.get("goes_to", ""),
        )
        for entry in raw["answers"]
    )
    by_key = {answer.key: answer for answer in answers}

    # A suggestion naming an answer that does not exist would be a chip that
    # does nothing when tapped, and it would fail silently at the one moment
    # somebody is looking for help. Caught here, at import, instead.
    suggested = {
        screen: tuple(keys) for screen, keys in raw.get("suggested", {}).items()
    }
    default = tuple(raw.get("default_suggestions", ()))
    for screen, keys in list(suggested.items()) + [("default", default)]:
        unknown = [k for k in keys if k not in by_key]
        if unknown:
            raise ValueError(
                f"{KNOWLEDGE_FILE.name}: suggestions for {screen!r} name "
                f"answers that do not exist: {', '.join(unknown)}"
            )

    return _Base(
        answers=answers,
        by_key=by_key,
        suggested=suggested,
        default_suggestions=default,
    )


def all_answers() -> tuple[Answer, ...]:
    return _base().answers


def by_key(key: str) -> Answer | None:
    return _base().by_key.get(key)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def score(question: str, answer: Answer) -> int:
    """How strongly a question asks for this answer.

    Phrases count for more than single words, because "room" alone is weak and
    "room rent limit" is not.
    """
    # Apostrophes are dropped so "don't have" and "dont have" are one thing.
    # People type both, and a trigger that only matches one of them is a
    # trigger that misses half the time.
    asked = question.lower().replace("’", "").replace("'", "")
    words = _words(asked)
    total = 0
    for trigger in answer.triggers:
        if " " in trigger or "-" in trigger:
            if trigger in asked:
                total += 3
        elif trigger in words:
            total += 1
    return total


def best_match(question: str, *, floor: int = 1) -> Answer | None:
    """The answer this question is asking for, or None if nothing fits."""
    ranked = sorted(all_answers(), key=lambda a: score(question, a), reverse=True)
    top = ranked[0]
    return top if score(question, top) >= floor else None


def suggestions_for(screen: str) -> list[Answer]:
    base = _base()
    keys = base.suggested.get(screen, base.default_suggestions)
    return [base.by_key[key] for key in keys]


def as_context() -> str:
    """The whole knowledge base, for grounding a model."""
    return "\n\n".join(f"[{a.key}] {a.question}\n{a.body}" for a in all_answers())
