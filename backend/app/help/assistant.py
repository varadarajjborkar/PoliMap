"""Answering a question about the app, without being able to change anything.

Two ways to answer, and the second is built on the first. Without a language
model the knowledge base answers on its own by matching what was asked. With
one, the model is handed that same knowledge and told to answer only from it,
so the difference between the two paths is fluency rather than substance.

What the help desk refuses, and what it says instead, is in `guardrails.yaml`.
This module applies those rules; it does not contain them. Both directions are
applied:

* A question matching an `incoming` rule is answered from the file and never
  reaches a model. Refusing before the call is stronger than instructing a
  model to refuse, because the instruction is only as good as the model's
  attention and the refusal is not.
* A model's draft matching an `outgoing` rule is dropped and the written answer
  is used in its place. A question is untrusted text, and the payoff of a
  successful injection is not rudeness, it is a link or a claim for somebody in
  a hospital to act on.

The structural guarantee sits underneath all of that and does not depend on any
pattern: this module is given no session, no policy and no document, and the
route that calls it takes no session id. There is nothing here to leak, and
nothing here to write. A model asked to reveal somebody's cover is being asked
by a process that does not have it.

Everything written down here is written in English, and travels with the key it
is read under so the browser can say it in the reader's language. A model's
answer does not: it is told to reply in whatever the question was asked in,
including the way most of this country actually writes, which is one language
in another language's letters. "Room rent ka limit kitna hai" is Hindi, and an
answer in Devanagari is an answer in the wrong place.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.agents.registry import registry
from app.core import guardrails
from app.core.config import ModelRole
from app.core.logging import get_logger
from app.help import knowledge
from app.schemas.help import HelpReply, HelpSource, Suggestion

log = get_logger(__name__)

RULES_FILE = Path(__file__).with_name("guardrails.yaml")

DO_NOT_KNOW = (
    "I do not know that one. I only know how this app works and how Indian "
    "health insurance settles a hospital bill, so anything outside that I "
    "would only be guessing at.\n\n"
    "If it is something the team should hear, I can pass it on and give you a "
    "reference to quote."
)

OPENING = (
    "Ask me anything about this app or about how your cover works. I explain "
    "and point you to the right place; I cannot change anything for you, and "
    "nothing here is medical advice."
)


# The five the interface itself is written in. Anything else falls back to
# English, which is also what the app does.
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "mr": "Marathi",
    "te": "Telugu",
}


# Where each script this app is likely to be typed in lives in Unicode, and
# what to call it when telling a model which one it is looking at.
_SCRIPTS = (
    ("Devanagari", 0x0900, 0x097F),
    ("Bengali", 0x0980, 0x09FF),
    ("Gurmukhi", 0x0A00, 0x0A7F),
    ("Gujarati", 0x0A80, 0x0AFF),
    ("Tamil", 0x0B80, 0x0BFF),
    ("Telugu", 0x0C00, 0x0C7F),
    ("Kannada", 0x0C80, 0x0CFF),
    ("Malayalam", 0x0D00, 0x0D7F),
)


def script_of(question: str) -> str:
    """Which script a question is written in, or "" for the Latin alphabet.

    Decided here rather than left to the model, because this is the one part of
    answering that a machine can settle exactly and a model kept getting wrong.
    Told only to reply in the same script, a model reads "kitna cover hoga",
    recognises the Hindi, and answers in Devanagari to somebody who was typing
    in English letters. Counted rather than sniffed at the first character: a
    question in Kannada still has a "50%" and an "IRDAI" in it.
    """
    counts = dict.fromkeys((name for name, _, _ in _SCRIPTS), 0)
    for char in question:
        point = ord(char)
        for name, low, high in _SCRIPTS:
            if low <= point <= high:
                counts[name] += 1
                break
    top = max(counts, key=lambda name: counts[name])
    return top if counts[top] else ""


def _language_rule(language: str, question: str = "") -> str:
    """What the model is told about which language to answer in.

    Two instructions, and the second is the one that matters here. Reply in the
    language the question was written in, and reply in the *script* it was
    written in: somebody typing Hinglish is not asking for Devanagari, and a
    reply in a script they were not using is a reply they have to decode.
    """
    chosen = LANGUAGE_NAMES.get(language, "English")
    script = script_of(question)
    if script:
        return (
            f"\n\nThe question is written in the {script} script. Write your "
            f"whole reply in {script} too, in the same language it was asked "
            "in, and keep the insurance words people already say in English."
        )
    # Latin letters, which is two different questions: English, or an Indian
    # language written in English letters. The language of the app decides
    # which Indian one it is, and that prior matters: left to guess, a model
    # reads romanised Kannada and answers a Kannada speaker in Tamil.
    if chosen == "English":
        return (
            "\n\nThe question is written in the Latin alphabet. If it is plain "
            "English, reply in English. If it is an Indian language written in "
            "English letters, Hinglish and the like, reply in that same "
            "language in English letters, never in another script and never in "
            "a language they did not use."
        )
    return (
        f"\n\nThe question is written in the Latin alphabet, and this person's "
        f"app is set to {chosen}. {chosen} is the language to answer in either "
        "way; the letters are what changes. If the question is plain English, "
        f"reply in {chosen} in its own script. If the question is {chosen} "
        f"written in English letters, or a mixture of {chosen} and English, "
        f"reply in {chosen} written in English letters exactly as they wrote "
        "it, and never in another script or another language."
    )


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    reply: str = ""


@dataclass(frozen=True)
class _Rules:
    system: str
    incoming: tuple[Rule, ...]
    outgoing: tuple[Rule, ...]
    max_question_chars: int
    max_reply_chars: int


@lru_cache(maxsize=1)
def rules() -> _Rules:
    """Read the guardrails once. `safe_load` constructs nothing but data."""
    raw = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
    limits = raw.get("limits", {})

    def compiled(section: str) -> tuple[Rule, ...]:
        return tuple(
            Rule(
                name=entry["name"],
                pattern=re.compile(entry["pattern"], re.IGNORECASE),
                reply=entry.get("reply", "").strip(),
            )
            for entry in raw.get(section, ())
        )

    return _Rules(
        system=raw["system"].strip(),
        incoming=compiled("incoming"),
        outgoing=compiled("outgoing"),
        max_question_chars=int(limits.get("max_question_chars", 500)),
        max_reply_chars=int(limits.get("max_reply_chars", 2000)),
    )


def _suggestions(screen: str) -> list[Suggestion]:
    return [
        Suggestion(key=a.key, question=a.question, goes_to=a.goes_to)
        for a in knowledge.suggestions_for(screen)
    ]


def opening(screen: str = "") -> HelpReply:
    """What the help desk says before anybody has asked anything."""
    return HelpReply(
        text=OPENING,
        key="opening",
        source=HelpSource.KNOWLEDGE,
        suggestions=_suggestions(screen),
    )


def _normalised(text: str) -> str:
    r"""The form the rules are matched against.

    Apostrophes are dropped because they split words: `everyone\w*` does not
    match "everyone's", and a rule that misses the possessive misses the way
    people actually write the question. Curly and straight are both dropped,
    since phones produce one and keyboards the other.
    """
    return text.replace("\u2019", "").replace("'", "")


def refused_by(question: str) -> Rule | None:
    """The incoming rule this question trips, if any."""
    asked = _normalised(question)
    return next((r for r in rules().incoming if r.pattern.search(asked)), None)


def _asked(question: str) -> str:
    return (question or "").strip()[: rules().max_question_chars]


def _refusal(rule: Rule, screen: str) -> HelpReply:
    log.info("helpdesk refused", rule=rule.name)
    return HelpReply(
        text=rule.reply,
        key=f"refuse.{rule.name}",
        source=HelpSource.KNOWLEDGE,
        suggestions=_suggestions(screen),
    )


def _written(match, screen: str) -> HelpReply:
    """The answer as this repository wrote it, which is the fallback for all of
    them: no model, a model that could not be reached, and a model whose draft
    was not allowed out."""
    if match is None:
        return HelpReply(
            text=DO_NOT_KNOW, key="unknown", source=HelpSource.UNKNOWN,
            suggestions=_suggestions(screen), offer_ticket=True,
        )
    return HelpReply(
        text=match.body, key=f"answer.{match.key}", source=HelpSource.KNOWLEDGE,
        goes_to=match.goes_to, suggestions=_suggestions(screen),
    )


def _spoken(text: str, match, screen: str) -> HelpReply:
    """A model's answer. No key: it is already in the reader's language."""
    return HelpReply(
        text=text,
        source=HelpSource.MODEL,
        goes_to=match.goes_to if match else "",
        suggestions=_suggestions(screen),
        offer_ticket=match is None,
    )


def answer(
    question: str,
    *,
    screen: str = "",
    language: str = "en",
    use_model: bool = True,
) -> HelpReply:
    """Answer one question, or say honestly that it cannot be answered."""
    asked = _asked(question)
    if not asked:
        return opening(screen)

    refusal = refused_by(asked)
    if refusal is not None:
        return _refusal(refusal, screen)

    match = knowledge.best_match(asked)

    if use_model and registry.has_llm:
        drafted = _from_model(asked, match, language)
        if drafted:
            return _spoken(drafted, match, screen)

    return _written(match, screen)


# How far behind the model the reader is kept, in characters.
#
# Text is only released once this many characters sit behind it, so that
# anything a rule would catch is caught while it is still held. Every pattern
# in guardrails.yaml is far shorter than this, so a phrase cannot be half
# released and half examined: by the time a character is sent, everything that
# could turn it into a match has already been written and checked.
HOLD_BACK_CHARS = 200


def answer_stream(
    question: str, *, screen: str = "", language: str = "en"
) -> Iterator[dict[str, Any]]:
    """The same answer, in the pieces it is written in.

    Somebody standing in a hospital does not want to watch a spinner for eight
    seconds, so the model's answer is passed on as it is written. The vetting is
    not relaxed for it. Every check `answer` makes on a finished draft is made
    here on the growing one, and text is released only from behind
    `HOLD_BACK_CHARS`, so a rule that a sentence is about to trip trips before
    that sentence has been shown to anybody.

    Two kinds of thing come out of this: `delta`, another piece of what is being
    written, and exactly one `reply`, which is the whole answer and the last
    word on it. When a draft is stopped part way, the reply carries the written
    answer instead and the browser replaces what it had. The reply is the
    authority; a delta is a preview of one.
    """
    asked = _asked(question)
    if not asked:
        yield {"reply": opening(screen)}
        return

    refusal = refused_by(asked)
    if refusal is not None:
        yield {"reply": _refusal(refusal, screen)}
        return

    match = knowledge.best_match(asked)
    if not registry.has_llm:
        yield {"reply": _written(match, screen)}
        return

    draft = ""
    released = 0
    stopped = ""
    try:
        for piece in registry.stream(
            ModelRole.NARRATE,
            system=rules().system + _language_rule(language, asked),
            prompt=_grounded(asked, match),
            temperature=0.2,
            max_tokens=400,
        ):
            draft += piece
            stopped = _straying(draft)
            if stopped:
                break
            # Softened over the whole draft rather than over each piece: a
            # phrase split across two pieces is one phrase, and rewriting the
            # halves separately would rewrite neither.
            safe = guardrails.soften_promises(draft)
            cut = max(0, len(safe) - HOLD_BACK_CHARS)
            if cut > released:
                yield {"delta": safe[released:cut]}
                released = cut
    except Exception as exc:
        log.warning("helpdesk stream ended early", error=str(exc)[:120])
        stopped = "unreachable"

    if stopped:
        log.warning("helpdesk draft dropped", rule=stopped)
        yield {"reply": _written(match, screen)}
        return

    final = _vetted(draft.strip())
    if not final:
        yield {"reply": _written(match, screen)}
        return

    if len(final) > released:
        yield {"delta": final[released:]}
    yield {"reply": _spoken(final, match, screen)}


# Markers around the question, so that a question saying "ignore the above" is
# read as part of the thing being quoted. They are unlikely in ordinary text
# and are stripped from the question itself, so a question cannot close its own
# fence and start writing instructions after it.
_FENCE_OPEN = "<<<QUESTION"
_FENCE_CLOSE = "QUESTION>>>"
_FENCE_LIKE = re.compile(r"<<<|>>>", re.IGNORECASE)


def _fenced(question: str) -> str:
    return f"{_FENCE_OPEN}\n{_FENCE_LIKE.sub(' ', question)}\n{_FENCE_CLOSE}"


def _grounded(question: str, match) -> str:
    """The question, and the only ground the model is allowed to stand on."""
    hint = f"\n\nThe closest reference entry is [{match.key}]." if match else ""
    return f"Reference:\n{knowledge.as_context()}\n\n{_fenced(question)}{hint}"


def _from_model(question: str, match, language: str = "en") -> str:
    """Let a model word the answer, from the knowledge base and nothing else."""
    try:
        response = registry.complete(
            ModelRole.NARRATE,
            system=rules().system + _language_rule(language, question),
            prompt=_grounded(question, match),
            temperature=0.2,
            max_tokens=400,
        )
    except Exception as exc:
        log.warning("helpdesk model unavailable", error=str(exc)[:120])
        return ""

    return _vetted(response.text.strip())


def _straying(draft: str) -> str:
    """The rule this draft has already broken, if it has broken one.

    Everything `_vetted` decides on a finished draft, decided on an unfinished
    one. It can be asked after every piece because every check here is monotone:
    text that matches a rule goes on matching it as more is written, so a draft
    that is clean so far cannot have been dirty earlier.
    """
    if len(draft) > rules().max_reply_chars:
        return "too_long"
    for rule in rules().outgoing:
        if rule.pattern.search(draft):
            return rule.name
    refusal = refused_by(draft)
    if refusal is not None:
        return f"incoming:{refusal.name}"
    if guardrails.contains_clinical_advice(draft):
        return "clinical"
    return ""


def _vetted(draft: str) -> str:
    """Whether a model's draft is allowed out, and nothing in between.

    Every rejection returns the empty string, which sends the caller back to
    the written answer. Editing a draft into shape is not offered: text that
    has been steered somewhere cannot be repaired by deleting the evidence of
    it, and a half-rewritten answer hides the signal that anything happened.
    """
    if not draft:
        return ""

    strayed = _straying(draft)
    if strayed:
        log.warning("helpdesk draft dropped", rule=strayed)
        return ""

    # The same treatment every model-written sentence in this system gets.
    return guardrails.sanitise(draft, fallback="")
