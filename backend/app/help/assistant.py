"""Answering a question about the app, without being able to change anything.

Two ways to answer, and the second is built on the first. Without a language
model the knowledge base answers on its own by matching what was asked. With
one, the model is handed that same knowledge and told to answer only from it,
so the difference between the two paths is fluency rather than substance.

Three things are refused outright, before any model sees them: anything
clinical, anything asking what an insurer will decide, and anything asking the
helpdesk to change something. The first two are the problem statement's own
boundaries. The third is this module's: there is no write path from here, so
saying yes would be a promise nothing could keep.

Whatever comes back from a model goes through the same guardrails as every
other model-written sentence in this system, and is dropped rather than
repaired if it strays.
"""

from __future__ import annotations

import re

from app.agents.registry import registry
from app.core import guardrails
from app.core.config import ModelRole
from app.core.logging import get_logger
from app.help import knowledge
from app.schemas.help import HelpReply, HelpSource, Suggestion

log = get_logger(__name__)

MAX_QUESTION = 500
"""Long enough for anything worth asking, short enough that a paste of a whole
policy is refused rather than sent to a model."""

SYSTEM = (
    "You are the help desk inside PoliMap, an app that estimates what an "
    "Indian hospital stay will cost somebody given their health insurance "
    "policy. You are talking to a person who may be standing in a hospital.\n\n"
    "Answer ONLY from the reference below. If the reference does not cover it, "
    "say plainly that you do not know and that they can raise it with the "
    "team. Never invent a figure, a policy term, or a feature of the app.\n\n"
    "You cannot change anything. You cannot edit their policy, record a cost, "
    "move their stay along or file a claim. You explain and you point at where "
    "in the app something is done.\n\n"
    "Never give medical or clinical advice of any kind. Never say what an "
    "insurer will decide; say what is likely and that only the insurer can "
    "decide a claim.\n\n"
    "Two or three short paragraphs at most. Plain words. No lists unless the "
    "answer is genuinely a list."
)

# Asked to do something rather than explain something.
_ASKS_FOR_ACTION = re.compile(
    r"\b(change|edit|update|set|fix|delete|remove|add|enter|fill|correct|"
    r"upload|record|submit|file)\b.{0,40}\b(for me|it for me|on my behalf|"
    r"yourself|please do)\b",
    re.IGNORECASE,
)
# A clinical question needs a clinical subject, not merely a clinical shape.
# "Should I have this surgery" is one; "whose name should I enter" is not, and
# an earlier version of this refused the second, which is the single question
# this help desk most exists to answer. "Doctor" is deliberately absent: asking
# whether a doctor's letter is needed for a claim is paperwork, not medicine.
_CLINICAL_SUBJECT = (
    r"surgery|operation|treatment|procedure|medicine|medication|drug|tablet|"
    r"injection|therapy|chemo\w*|dialysis|symptom|pain|fever|infection"
)
_ASKS_CLINICAL = re.compile(
    rf"\b(?:should i|do i need|is it safe|is it necessary|is it risky)\b"
    rf"(?=.*\b(?:{_CLINICAL_SUBJECT})\b)"
    r"|\b(?:diagnos|prescri)\w*"
    r"|\bwhat is wrong with\b"
    r"|\bwhich (?:treatment|surgery|doctor|medicine|procedure)\b"
    r"|\bis it safe\b",
    re.IGNORECASE,
)
_ASKS_FOR_A_RULING = re.compile(
    r"\b(will (?:they|my insurer|the insurer|the company) (?:pay|approve|"
    r"reject|cover)|am i covered|is this covered|guarantee)\b",
    re.IGNORECASE,
)

CANNOT_ACT = (
    "I cannot change anything in the app myself, on purpose: everything here "
    "is what your claim gets estimated from, so it stays in your hands. Tell "
    "me what you are trying to do and I will point you at where to do it."
)

NOT_CLINICAL = (
    "That is a medical question and I am the wrong place for it. This app "
    "handles the money and the paperwork side of an admission and nothing "
    "clinical, so please ask the treating doctor or the hospital.\n\n"
    "If it was really about what your policy covers for a treatment, ask me "
    "that instead and I can help."
)

NOT_A_RULING = (
    "Only your insurer can decide a claim, so I cannot tell you what they will "
    "do. What this app can show you is what your policy says and what that "
    "usually means in rupees, which is the thing to take to them.\n\n"
    "Ask me about a particular part of your cover and I will explain how it "
    "works."
)

DO_NOT_KNOW = (
    "I do not know that one. I only know how this app works and how Indian "
    "health insurance settles a hospital bill, so anything outside that I "
    "would only be guessing at.\n\n"
    "If it is something the team should hear, I can pass it on and give you a "
    "reference to quote."
)


def _suggestions(screen: str) -> list[Suggestion]:
    return [
        Suggestion(key=a.key, question=a.question, goes_to=a.goes_to)
        for a in knowledge.suggestions_for(screen)
    ]


def opening(screen: str = "") -> HelpReply:
    """What the helpdesk says before anybody has asked anything."""
    return HelpReply(
        text=(
            "Ask me anything about this app or about how your cover works. I "
            "explain and point you to the right place; I cannot change "
            "anything for you, and nothing here is medical advice."
        ),
        source=HelpSource.KNOWLEDGE,
        suggestions=_suggestions(screen),
    )


def answer(question: str, *, screen: str = "", use_model: bool = True) -> HelpReply:
    """Answer one question, or say honestly that it cannot be answered."""
    asked = (question or "").strip()[:MAX_QUESTION]
    if not asked:
        return opening(screen)

    if _ASKS_CLINICAL.search(asked):
        return HelpReply(
            text=NOT_CLINICAL, source=HelpSource.KNOWLEDGE,
            suggestions=_suggestions(screen),
        )
    if _ASKS_FOR_ACTION.search(asked):
        return HelpReply(
            text=CANNOT_ACT, source=HelpSource.KNOWLEDGE,
            suggestions=_suggestions(screen),
        )
    if _ASKS_FOR_A_RULING.search(asked):
        return HelpReply(
            text=NOT_A_RULING, source=HelpSource.KNOWLEDGE,
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


def _from_model(question: str, match) -> str:
    """Let a model word the answer, from the knowledge base and nothing else."""
    reference = knowledge.as_context()
    hint = f"\n\nThe closest reference entry is [{match.key}]." if match else ""
    try:
        response = registry.complete(
            ModelRole.NARRATE,
            system=SYSTEM,
            prompt=f"Reference:\n{reference}\n\nQuestion: {question}{hint}",
            temperature=0.2,
            max_tokens=400,
        )
    except Exception as exc:
        log.warning("helpdesk model unavailable", error=str(exc)[:120])
        return ""

    # The same treatment every model-written sentence in this system gets. A
    # dropped answer falls back to the knowledge base rather than to nothing.
    clean = guardrails.sanitise(response.text.strip(), fallback="")
    return clean
