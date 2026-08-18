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
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

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
        text=OPENING, source=HelpSource.KNOWLEDGE, suggestions=_suggestions(screen)
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


def answer(question: str, *, screen: str = "", use_model: bool = True) -> HelpReply:
    """Answer one question, or say honestly that it cannot be answered."""
    asked = (question or "").strip()[: rules().max_question_chars]
    if not asked:
        return opening(screen)

    refusal = refused_by(asked)
    if refusal is not None:
        log.info("helpdesk refused", rule=refusal.name)
        return HelpReply(
            text=refusal.reply,
            source=HelpSource.KNOWLEDGE,
            suggestions=_suggestions(screen),
        )

    match = knowledge.best_match(asked)

    if use_model and registry.has_llm:
        drafted = _from_model(asked, match)
        if drafted:
            return HelpReply(
                text=drafted,
                source=HelpSource.MODEL,
                goes_to=match.goes_to if match else "",
                suggestions=_suggestions(screen),
                offer_ticket=match is None,
            )

    if match is None:
        return HelpReply(
            text=DO_NOT_KNOW, source=HelpSource.UNKNOWN,
            suggestions=_suggestions(screen), offer_ticket=True,
        )
    return HelpReply(
        text=match.body, source=HelpSource.KNOWLEDGE, goes_to=match.goes_to,
        suggestions=_suggestions(screen),
    )


# Markers around the question, so that a question saying "ignore the above" is
# read as part of the thing being quoted. They are unlikely in ordinary text
# and are stripped from the question itself, so a question cannot close its own
# fence and start writing instructions after it.
_FENCE_OPEN = "<<<QUESTION"
_FENCE_CLOSE = "QUESTION>>>"
_FENCE_LIKE = re.compile(r"<<<|>>>", re.IGNORECASE)


def _fenced(question: str) -> str:
    return f"{_FENCE_OPEN}\n{_FENCE_LIKE.sub(' ', question)}\n{_FENCE_CLOSE}"


def _from_model(question: str, match) -> str:
    """Let a model word the answer, from the knowledge base and nothing else."""
    hint = f"\n\nThe closest reference entry is [{match.key}]." if match else ""
    try:
        response = registry.complete(
            ModelRole.NARRATE,
            system=rules().system,
            prompt=(
                f"Reference:\n{knowledge.as_context()}\n\n"
                f"{_fenced(question)}{hint}"
            ),
            temperature=0.2,
            max_tokens=400,
        )
    except Exception as exc:
        log.warning("helpdesk model unavailable", error=str(exc)[:120])
        return ""

    return _vetted(response.text.strip())


def _vetted(draft: str) -> str:
    """Whether a model's draft is allowed out, and nothing in between.

    Every rejection returns the empty string, which sends the caller back to
    the written answer. Editing a draft into shape is not offered: text that
    has been steered somewhere cannot be repaired by deleting the evidence of
    it, and a half-rewritten answer hides the signal that anything happened.
    """
    if not draft:
        return ""

    if len(draft) > rules().max_reply_chars:
        log.warning("helpdesk draft dropped", rule="too_long", chars=len(draft))
        return ""

    for rule in rules().outgoing:
        if rule.pattern.search(draft):
            log.warning("helpdesk draft dropped", rule=rule.name)
            return ""

    # A question that got past the incoming rules can still produce an answer
    # that trips them, which is the shape a successful injection takes: the
    # request looks ordinary and the reply is the part that strayed.
    refusal = refused_by(draft)
    if refusal is not None:
        log.warning("helpdesk draft dropped", rule=f"incoming:{refusal.name}")
        return ""

    # The same treatment every model-written sentence in this system gets.
    return guardrails.sanitise(draft, fallback="")
