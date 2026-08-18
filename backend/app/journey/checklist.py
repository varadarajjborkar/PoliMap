"""What to do at this stage of this admission, under this policy.

Generic advice about hospital admissions is available everywhere and helps
nobody: "keep your documents safe" is true of every policy ever written. What
is not available anywhere is the same advice with this family's numbers in it,
and that is the only kind worth putting on a screen somebody is reading in a
corridor.

So every item here is derived from the compiled policy and the stay so far. A
room cap becomes the figure to ask the admission desk for. A diagnostics
sub-limit becomes the number to quote before consenting to a scan. A
post-hospitalisation window becomes a date to keep receipts until. Where the
policy says nothing about a thing, the item for it is not shown, because an
instruction that does not apply costs the reader the same attention as one that
does.

Ticks are kept on the journey, so the list is a record of what was done rather
than a poster that resets on every reload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app.schemas.journey import JourneyStage, JourneyState
from app.schemas.money import format_inr
from app.schemas.policy import ExpenseHead, NormalizedPolicy
from app.schemas.simulation import SettlementMode


@dataclass
class ChecklistItem:
    """One thing to do, and the reason it is worth doing."""

    item_id: str
    text: str
    why: str = ""
    urgent: bool = False
    """Shown first, and marked. Reserved for the few where being late costs
    money rather than convenience."""
    done: bool = False
    tags: list[str] = field(default_factory=list)


def items_for(
    state: JourneyState,
    policy: NormalizedPolicy,
    *,
    settlement: SettlementMode | None = None,
) -> list[ChecklistItem]:
    """The list for where this admission has got to."""
    builder = _BUILDERS.get(state.stage)
    items = builder(state, policy, settlement) if builder else []

    done = set(state.checklist_done)
    for item in items:
        item.done = item.item_id in done

    items.sort(key=lambda i: (i.done, not i.urgent))
    return items


def progress(items: list[ChecklistItem]) -> tuple[int, int]:
    return sum(1 for item in items if item.done), len(items)


# --- per stage --------------------------------------------------------------


def _pre_admission(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    items = [
        ChecklistItem(
            "carry_card",
            "Carry the policy document or e-card, and a photo ID for the patient",
            "The insurance desk cannot start a cashless request without both.",
            urgent=True,
        ),
        ChecklistItem(
            "confirm_network",
            f"Ask the hospital to confirm they are in "
            f"{policy.meta.insurer_name or 'your insurer'}'s cashless network "
            f"for this treatment",
            "Network lists change, and the one place it matters is the counter.",
            urgent=True,
        ),
    ]

    cap = _room_cap(policy)
    if cap:
        items.append(ChecklistItem(
            "ask_for_room",
            f"Ask for a room at or under {cap} a day",
            "A costlier room does not only cost the difference: your insurer "
            "then pays a reduced share of the surgeon, theatre and nursing "
            "charges as well.",
            urgent=True,
        ))

    if policy.pre_hospitalisation_days:
        items.append(ChecklistItem(
            "gather_pre_bills",
            f"Gather bills from the last {policy.pre_hospitalisation_days} days: "
            f"consultations, tests, medicines",
            "Those are claimable as pre-hospitalisation expenses, and they are "
            "the ones most often thrown away.",
        ))

    if not policy.covers_consumables:
        items.append(ChecklistItem(
            "expect_consumables",
            "Expect to pay for gloves, syringes, and similar items yourself",
            "This policy does not cover consumables. On a surgical admission "
            "they commonly run to several thousand rupees.",
        ))

    return items


def _admitted(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    items = [
        ChecklistItem(
            "check_room_rate",
            "Check the room rate written on the admission form",
            "It is the single number that decides how much of the rest of the "
            "bill your insurer pays. Correct it now if it is wrong; nobody "
            "will revisit it at discharge.",
            urgent=True,
        ),
        ChecklistItem(
            "keep_receipts",
            "Start keeping every receipt, including the pharmacy counter ones",
            "Reimbursement is refused for anything without an original bill.",
        ),
    ]

    cap = _room_cap(policy)
    if cap and state.room_rate_per_day:
        items.append(ChecklistItem(
            "room_within_cap",
            f"Confirm the room you are in bills at or under {cap} a day",
            f"You were admitted at {format_inr(state.room_rate_per_day)}. "
            f"Moving room is easiest on the first day and hardest on the last.",
            urgent=True,
        ))

    return items


def _investigation(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    items = [
        ChecklistItem(
            "ask_cost_first",
            "Ask what each scan or test costs before agreeing to it",
            "Investigations are where a bill grows fastest and where a "
            "sub-limit is most often crossed without anybody saying so.",
        ),
    ]

    limit = policy.sublimit_for(ExpenseHead.INVESTIGATIONS)
    if limit and limit.amount:
        spent = state.accrued_by_head().get(ExpenseHead.INVESTIGATIONS)
        items.insert(0, ChecklistItem(
            "diagnostics_sublimit",
            f"Tell the doctor your policy caps tests and scans at "
            f"{format_inr(limit.amount)}",
            (
                f"You have used {format_inr(spent)} of it so far. "
                if spent else ""
            ) + "Anything above the cap is yours to pay in full.",
            urgent=True,
        ))

    return items


def _pre_auth(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    return [
        ChecklistItem(
            "chase_preauth",
            "Chase the approval, by name, at the hospital insurance desk",
            "A request sitting unread is the commonest reason a cashless "
            "admission turns into a cash one.",
            urgent=True,
        ),
        ChecklistItem(
            "read_approved_amount",
            "Ask what amount was approved, not just whether it was approved",
            "Insurers frequently approve less than the estimate. The gap is "
            "yours, and it is better known now than at discharge.",
            urgent=True,
        ),
        ChecklistItem(
            "keep_approval",
            "Keep a photograph of the approval letter",
            "It is the document that settles an argument at the billing "
            "counter five days from now.",
        ),
    ]


def _procedure(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    items = [
        ChecklistItem(
            "implant_invoice",
            "Ask for the implant or device invoice and its sticker",
            "Implants are claimed separately and are refused without the "
            "manufacturer's invoice. There is no way to obtain it later.",
            urgent=True,
        ),
        ChecklistItem(
            "consent_costs",
            "Ask whether anything on the consent form is billed separately",
            "Surgeon, anaesthetist and theatre are often three bills, and only "
            "the first is quoted.",
        ),
    ]
    if not policy.covers_consumables:
        items.append(ChecklistItem(
            "consumables_running",
            "Ask the ward to keep the consumables list itemised",
            "You are paying for these, so an itemised list is the only way to "
            "check the count at discharge.",
        ))
    return items


def _recovery(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    return [
        ChecklistItem(
            "daily_bill",
            "Ask for an interim bill every day, and read it",
            "A charge queried on the day it appears is corrected. The same "
            "charge queried at discharge is defended.",
            urgent=True,
        ),
        ChecklistItem(
            "watch_the_room",
            "Ask before any move to a different room or to ICU",
            "A change of room changes the daily rate, and with it the share "
            "your insurer pays on everything room-linked.",
        ),
    ]


def _discharge_planning(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    """The list that decides whether the claim is paid.

    Almost everything here is impossible to do afterwards. A discharge summary
    can be requested again; an itemised bill from a hospital that has already
    been paid, in practice, cannot.
    """
    items = [
        ChecklistItem(
            "discharge_summary",
            "Collect the discharge summary, signed and stamped",
            "No claim is settled without it. Check it names the treatment and "
            "the dates of admission and discharge.",
            urgent=True,
            tags=["paperwork"],
        ),
        ChecklistItem(
            "itemised_bill",
            "Collect the final bill itemised, not the one-line total",
            "A single figure cannot be checked against your policy, and an "
            "insurer will query it. Ask for the breakdown before you pay.",
            urgent=True,
            tags=["paperwork"],
        ),
        ChecklistItem(
            "originals",
            "Collect original reports, prescriptions and pharmacy receipts",
            "Originals, not photocopies. Reimbursement claims are refused "
            "without them, and the hospital keeps no second set.",
            urgent=True,
            tags=["paperwork"],
        ),
        ChecklistItem(
            "check_non_payables",
            "Check the bill for items your insurer never pays",
            "Gloves, gowns, administration and record charges are on the IRDAI "
            "non-payable list. They belong on your side of the bill, but they "
            "are sometimes on the insurer's, and the hospital will correct it.",
            urgent=True,
        ),
    ]

    if state.room_rate_per_day and _room_cap(policy):
        items.append(ChecklistItem(
            "check_deduction",
            "Check how the proportionate deduction was worked out",
            "It applies to room-linked charges only: room, nursing, doctor "
            "visits, surgeon, theatre. Since the IRDAI circular of May 2024 it "
            "must not touch medicines, tests, implants or ICU.",
            urgent=True,
        ))

    if policy.post_hospitalisation_days:
        items.append(ChecklistItem(
            "post_window",
            f"Keep every prescription and bill for the next "
            f"{policy.post_hospitalisation_days} days"
            + (
                f", until {(state.admitted_at.date() + timedelta(days=policy.post_hospitalisation_days)):%d %B}"
                if state.admitted_at else ""
            ),
            "Follow-up consultations, medicines and tests in that window are "
            "claimable, and they are the part of a claim most often lost "
            "simply because the receipts were thrown away.",
            tags=["paperwork"],
        ))

    if settlement is SettlementMode.REIMBURSEMENT:
        items.append(ChecklistItem(
            "claim_deadline",
            "Ask your insurer the deadline for submitting the claim",
            "Reimbursement claims have a filing window, commonly fifteen to "
            "thirty days from discharge, and a late claim is refused on the "
            "date alone.",
            urgent=True,
        ))
    else:
        items.append(ChecklistItem(
            "final_approval",
            "Wait for the final approval before signing the discharge bill",
            "The last approval often differs from the pre-authorisation. What "
            "you sign for is what you owe.",
        ))

    return items


def _settled(
    state: JourneyState, policy: NormalizedPolicy, settlement: SettlementMode | None
) -> list[ChecklistItem]:
    return [
        ChecklistItem(
            "settlement_letter",
            "Keep the settlement letter with the bills",
            "It states what was paid and what was deducted, and it is what any "
            "dispute is argued from.",
        ),
        ChecklistItem(
            "check_deductions",
            "Check each deduction on the settlement against your policy",
            "A deduction that does not match a clause in your own document is "
            "worth querying. Insurers do correct them.",
        ),
        ChecklistItem(
            "note_remaining",
            "Note what cover is left for the rest of the policy year",
            "It is what any admission before your renewal date has to fit "
            "inside.",
        ),
    ]


_BUILDERS = {
    JourneyStage.PRE_ADMISSION: _pre_admission,
    JourneyStage.ADMITTED: _admitted,
    JourneyStage.INVESTIGATION: _investigation,
    JourneyStage.PRE_AUTH: _pre_auth,
    JourneyStage.PROCEDURE: _procedure,
    JourneyStage.RECOVERY: _recovery,
    JourneyStage.DISCHARGE_PLANNING: _discharge_planning,
    JourneyStage.SETTLED: _settled,
}


def _room_cap(policy: NormalizedPolicy) -> str:
    """The daily room entitlement in words, or nothing if there is no cap."""
    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    return format_inr(cap) if cap else ""
