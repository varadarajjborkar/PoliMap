"""What the helpdesk is allowed to know.

Every answer here is about *this app* or about how Indian health insurance
works, and every one of them is written in this repository rather than produced
on demand. That is the point. A person in a hospital corridor asking "whose
name do I put here" needs the answer this app actually expects, not a plausible
one, and the difference between those two is invisible to the person asking.

So the knowledge base does two jobs. Without a language model it answers on its
own, by matching what was asked against what is here. With one, it is the
ground the model is given: the model may reword and choose between these, and
is told plainly that anything not here is something it does not know.

Nothing in here is clinical, and nothing states what an insurer will do. Both
are checked again on the way out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Answer:
    """One thing the helpdesk can say, and how to tell it is being asked."""

    key: str
    question: str
    """The question as somebody would actually ask it, for the suggestion chips."""
    body: str
    triggers: tuple[str, ...]
    """Words that mean this is being asked. Matched as whole words."""
    goes_to: str = ""
    """Where in the app this is about, if anywhere: a step id."""
    tags: tuple[str, ...] = field(default_factory=tuple)


ANSWERS: tuple[Answer, ...] = (
    Answer(
        key="whose_name",
        question="Whose name should I enter?",
        body=(
            "Yours, whoever you are. The name is only a label for this device: "
            "it decides which set of admissions opens when you come back, and "
            "it is not sent anywhere or checked against anything.\n\n"
            "So if you are handling this for a parent, a neighbour or a friend, "
            "use your own name and track their admission under it. The patient "
            "is identified separately, from the policy itself: where a policy "
            "covers several people you pick which of them is being admitted, "
            "and that is the choice that changes the money, because age can "
            "change the co-payment."
        ),
        triggers=("name", "username", "who", "whose", "sign in", "login", "patient name"),
        goes_to="upload",
    ),
    Answer(
        key="which_document",
        question="Which document should I upload?",
        body=(
            "The policy schedule is the one that matters. It is the page with "
            "your own figures on it: sum insured, room rent limit, policy "
            "number, the people covered. The wording booklet is generic terms "
            "and is useful but secondary.\n\n"
            "If you have both, add both: they are read together and the "
            "schedule takes precedence where they disagree. A photograph works "
            "if it is square-on and readable. So does the PDF your insurer "
            "emailed, and that reads exactly."
        ),
        triggers=("document", "upload", "which file", "schedule", "wording", "pdf",
                  "photo", "policy document"),
        goes_to="upload",
    ),
    Answer(
        key="no_document",
        question="I do not have my policy document.",
        body=(
            "You can enter the figures by hand instead. The three that carry "
            "most of the answer are the sum insured, the room rent limit and "
            "any co-payment, and they are all printed on an insurance card or "
            "available from your insurer's app.\n\n"
            "Anything you leave out is treated as unknown rather than as zero, "
            "and the estimate says where it is unsure."
        ),
        triggers=("no document", "lost", "manual", "by hand", "without",
                  "do not have", "dont have", "do not have my policy",
                  "dont have my policy", "lost my policy", "no policy document"),
        goes_to="upload",
    ),
    Answer(
        key="pre_existing",
        question="What counts as a pre-existing condition?",
        body=(
            "A condition you already had when the policy started, whether or "
            "not it had been diagnosed then. Most Indian policies do not pay "
            "for one until a waiting period has passed, commonly two to four "
            "years from the start date.\n\n"
            "Only you can answer it, which is why you are asked rather than "
            "the document being read for it. If you are unsure, the honest "
            "answer is the one that matches what a doctor recorded before the "
            "policy began. Answering it wrongly on a claim form is what gets "
            "claims rejected later."
        ),
        triggers=("pre-existing", "pre existing", "existing", "before", "already had",
                  "waiting period", "ped"),
    ),
    Answer(
        key="room_limit",
        question="Why does the room I pick change the whole bill?",
        body=(
            "Because Indian policies cap the room rent per day, and taking a "
            "room above that cap does not only cost you the difference in "
            "rent. It reduces what the insurer pays on everything priced by "
            "room tier: nursing, doctor visits, the surgeon, the theatre. That "
            "is the proportionate deduction, and it is the single most "
            "expensive thing most people have never heard of.\n\n"
            "Since the IRDAI circular of May 2024 it must not touch medicines, "
            "tests, implants or intensive care. If a bill reduces those by the "
            "same fraction, that is worth querying."
        ),
        triggers=("room", "proportionate", "deduction", "cap", "rent", "category",
                  "why so expensive", "upgrade", "ward", "twin", "sharing",
                  "private", "general ward", "which room"),
        goes_to="policy",
    ),
    Answer(
        key="cashless",
        question="What is the difference between cashless and reimbursement?",
        body=(
            "Cashless means the insurer settles with the hospital directly and "
            "you pay only your own share. Reimbursement means you pay the "
            "whole bill first and claim it back afterwards, which can take "
            "weeks.\n\n"
            "The difference decides whether a hospital is usable at all, "
            "because it is the difference between finding your share and "
            "finding the entire bill on the day of admission. Every option is "
            "labelled with which one applies and with the cash you would need "
            "up front."
        ),
        triggers=("cashless", "reimbursement", "network", "upfront", "advance",
                  "pay first"),
        goes_to="search",
    ),
    Answer(
        key="second_policy",
        question="I have two policies. Can I use both?",
        body=(
            "Yes, and it is common: an employer group cover beside a personal "
            "one, or a top-up above a base policy. Add the second on the cover "
            "screen and both are settled in sequence against their own terms.\n\n"
            "Order matters and is not yours to choose. A top-up sits above a "
            "deductible, so it settles after the policy below it, and its "
            "deductible counts against the whole bill rather than only the "
            "part reaching it."
        ),
        triggers=("two policies", "second policy", "another policy", "employer",
                  "group cover", "top up", "top-up", "both"),
        goes_to="policy",
    ),
    Answer(
        key="wrong_figure",
        question="A figure was read wrong. Can I correct it?",
        body=(
            "Yes, and you should. On the cover screen every figure the "
            "document produced can be corrected, and a correction outranks "
            "what was extracted, so the system stops asking about it.\n\n"
            "It takes the forms a document uses: \"5 lakh\", \"5,00,000\", "
            "\"1%\" for a room limit expressed as a percentage, or a room "
            "category by name. Everything downstream is recomputed from it."
        ),
        triggers=("wrong", "incorrect", "mistake", "correct", "edit", "change",
                  "misread", "fix"),
        goes_to="policy",
    ),
    Answer(
        key="cover_left",
        question="I have claimed already this year. Does that matter?",
        body=(
            "It matters a great deal, and no document can know it: a schedule "
            "states the cover you bought, not the cover you have left. Set "
            "\"cover left this year\" on the cover screen and every estimate "
            "after it uses the balance.\n\n"
            "Without that, an estimate quietly assumes a year with no claims, "
            "which is the most optimistic possible reading."
        ),
        triggers=("claimed", "already used", "cover left", "balance", "remaining",
                  "used up", "exhausted"),
        goes_to="policy",
    ),
    Answer(
        key="bill_check",
        question="How do I check the final bill?",
        body=(
            "On the stay screen, photograph the itemised bill, not the "
            "one-line total. It is read line by line and checked against the "
            "IRDAI list of items no policy pays and against your own cover.\n\n"
            "The part worth knowing: some items are already inside the room or "
            "procedure charge under the regulator's own schedule, so billing "
            "them separately charges you twice for one thing. Each finding "
            "comes with a sentence you can say at the counter."
        ),
        triggers=("bill", "final bill", "discharge bill", "itemised", "itemized",
                  "check bill", "overcharge", "billing"),
        goes_to="journey",
    ),
    Answer(
        key="non_payable",
        question="What are non-payable items?",
        body=(
            "A published IRDAI list of things no health policy reimburses: "
            "gloves, gowns, registration and record charges, attendant and "
            "telephone charges, and similar. They are legitimately yours to "
            "pay.\n\n"
            "A separate part of the same schedule is more useful: items that "
            "are already included in the room charge, the procedure charge or "
            "the cost of treatment. Those should not appear as separate lines "
            "at all, and a billing desk will remove them if asked."
        ),
        triggers=("non payable", "non-payable", "not covered", "irdai", "gloves",
                  "consumables", "excluded"),
        goes_to="journey",
    ),
    Answer(
        key="claim_papers",
        question="What papers do I need for the claim?",
        body=(
            "The discharge summary signed and stamped, the itemised final "
            "bill rather than the one-line total, and the original reports, "
            "prescriptions and pharmacy receipts. Originals, not photocopies: "
            "reimbursement claims are refused without them and the hospital "
            "keeps no second set.\n\n"
            "The stay screen carries the list for wherever you have got to, "
            "and ticks off as you collect them. Keep every prescription and "
            "bill for the post-hospitalisation window too, usually 60 days: "
            "that is the part of a claim most often lost, simply because the "
            "receipts were thrown away."
        ),
        triggers=("papers", "documents for claim", "discharge summary", "receipts",
                  "originals", "letter", "certificate", "what do i need",
                  "paperwork", "claim form"),
        goes_to="journey",
    ),
    Answer(
        key="privacy",
        question="Where does my data go?",
        body=(
            "Your admission lives on this device. The server holds a working "
            "copy while you are using it and expires it within hours; the "
            "durable copy is the one in this browser, under the name you "
            "chose.\n\n"
            "Page images of an uploaded document are not kept past their "
            "session. Clearing a stay, or clearing everything under a name in "
            "Settings, removes it from this device."
        ),
        triggers=("data", "privacy", "stored", "server", "delete", "account",
                  "safe", "secure"),
    ),
    Answer(
        key="what_this_is",
        question="What can this app actually tell me?",
        body=(
            "What a hospital stay is likely to cost you, given your policy: "
            "which hospitals your cover works at, what room you are entitled "
            "to, what the insurer would pay and what you would find yourself. "
            "Then it tracks the stay and checks the final bill.\n\n"
            "What it cannot do is anything clinical. It does not diagnose, "
            "does not recommend a treatment or a hospital on medical grounds, "
            "and nothing it says binds an insurer. Every figure is an estimate "
            "and is labelled as one."
        ),
        triggers=("what is this", "what can", "help", "how does", "about", "purpose"),
    ),
)

BY_KEY = {answer.key: answer for answer in ANSWERS}

# Questions worth offering before anybody types, per screen.
SUGGESTED: dict[str, tuple[str, ...]] = {
    "upload": ("whose_name", "which_document", "no_document"),
    "policy": ("wrong_figure", "room_limit", "cover_left", "second_policy"),
    "search": ("cashless", "pre_existing", "room_limit"),
    "journey": ("bill_check", "non_payable", "privacy"),
}
DEFAULT_SUGGESTIONS = ("what_this_is", "whose_name", "room_limit")


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
    asked = question.lower().replace("\u2019", "").replace("'", "")
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
    ranked = sorted(ANSWERS, key=lambda a: score(question, a), reverse=True)
    top = ranked[0]
    return top if score(question, top) >= floor else None


def suggestions_for(screen: str) -> list[Answer]:
    keys = SUGGESTED.get(screen, DEFAULT_SUGGESTIONS)
    return [BY_KEY[key] for key in keys if key in BY_KEY]


def as_context() -> str:
    """The whole knowledge base, for grounding a model."""
    return "\n\n".join(f"[{a.key}] {a.question}\n{a.body}" for a in ANSWERS)
