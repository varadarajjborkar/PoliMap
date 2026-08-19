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

Kept short on purpose. This is read standing up, by somebody who has not slept,
between two conversations they are dreading. Every sentence here has to earn
the seconds it takes to read, so each item is one instruction and one reason,
and anything that was only there for completeness is gone.

Ticks are kept on the journey, so the list is a record of what was done rather
than a poster that resets on every reload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app.schemas.journey import JourneyStage, JourneyState
from app.schemas.money import ZERO, format_inr
from app.schemas.policy import ExpenseHead, NormalizedPolicy
from app.schemas.procedure import Procedure
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

    key: str = ""
    """What the reader's own language is looked up under, where it differs from
    `item_id`. Two wordings of one instruction are one task and must share a
    tick, so the id stays put and the key moves."""
    values: dict[str, str] = field(default_factory=dict)
    """The figures written into the sentence above, sent alongside it so the
    same sentence can be rebuilt in another language rather than translated
    after the numbers are already baked into it."""

    @property
    def string_key(self) -> str:
        return self.key or self.item_id


def items_for(
    state: JourneyState,
    policy: NormalizedPolicy,
    *,
    settlement: SettlementMode | None = None,
    procedure: Procedure | None = None,
) -> list[ChecklistItem]:
    """The list for where this admission has got to."""
    builder = _BUILDERS.get(state.stage)
    items = builder(state, policy, settlement, procedure) if builder else []

    done = set(state.checklist_done)
    for item in items:
        item.done = item.item_id in done

    items.sort(key=lambda i: (i.done, not i.urgent))
    return items


def progress(items: list[ChecklistItem]) -> tuple[int, int]:
    return sum(1 for item in items if item.done), len(items)


# --- per stage --------------------------------------------------------------


def _pre_admission(
    state: JourneyState,
    policy: NormalizedPolicy,
    settlement: SettlementMode | None,
    procedure: Procedure | None,
) -> list[ChecklistItem]:
    insurer = policy.meta.insurer_name or "your insurer"
    items = [
        ChecklistItem(
            "carry_card",
            "Carry your policy card and the patient's photo ID",
            "The desk cannot start a cashless claim without both.",
            urgent=True,
        ),
        ChecklistItem(
            "confirm_network",
            f"Ask the hospital if {insurer} cashless works here for this treatment",
            "Network lists change. The counter is where it counts.",
            urgent=True,
            values={"insurer": insurer},
        ),
    ]

    cap = _room_cap(policy)
    if cap:
        items.append(ChecklistItem(
            "ask_for_room",
            f"Ask for a room at {cap} a day or less",
            "A costlier room also cuts what you get on the surgeon, theatre "
            "and nursing, not just the room.",
            urgent=True,
            values={"cap": cap},
        ))

    if policy.pre_hospitalisation_days:
        days = str(policy.pre_hospitalisation_days)
        items.append(ChecklistItem(
            "gather_pre_bills",
            f"Collect bills from the last {days} days: visits, tests, medicines",
            "These are claimable, and the ones most often thrown away.",
            values={"days": days},
        ))

    if not policy.covers_consumables:
        items.append(ChecklistItem(
            "expect_consumables",
            "Expect to pay for gloves, syringes and the like",
            "This policy does not cover them. On surgery they often run to a "
            "few thousand rupees.",
        ))

    return items


def _admitted(
    state: JourneyState,
    policy: NormalizedPolicy,
    settlement: SettlementMode | None,
    procedure: Procedure | None,
) -> list[ChecklistItem]:
    """One list for the whole admission.

    Tests, the operation and recovery used to be three stages with a list each,
    which meant an item was hidden until somebody moved a marker, and the marker
    told the system nothing it did not already know. Every one of these is live
    from admission to discharge, so they are all shown, and the ones that do not
    apply are absent on the facts rather than on the stage: an implant invoice
    is asked for when the treatment uses an implant, not when a stage is tapped.
    """
    items = [
        ChecklistItem(
            "check_room_rate",
            "Check the room rate on the admission form",
            "This one number decides how much of the rest of the bill is paid. "
            "Fix it now; nobody checks it at discharge.",
            urgent=True,
        ),
        ChecklistItem(
            "keep_receipts",
            "Keep every receipt, pharmacy ones too",
            "Nothing is repaid without the original bill.",
        ),
        ChecklistItem(
            "daily_bill",
            "Ask for the bill every day, and read it",
            "A charge questioned the same day gets corrected. At discharge it "
            "gets defended.",
            urgent=True,
        ),
        ChecklistItem(
            "ask_cost_first",
            "Ask what each test or scan costs before agreeing",
            "Tests are where a bill grows fastest and a limit is crossed "
            "without anyone saying so.",
        ),
        ChecklistItem(
            "watch_the_room",
            "Ask before any move to another room or to ICU",
            "A new room means a new daily rate, and a new share on everything "
            "priced by room.",
        ),
    ]

    cap = _room_cap(policy)
    if cap and state.room_rate_per_day:
        rate = format_inr(state.room_rate_per_day)
        items.insert(1, ChecklistItem(
            "room_within_cap",
            f"Check your room bills at {cap} a day or less",
            f"You were admitted at {rate}. Moving is easy on day one and hard "
            f"on the last.",
            urgent=True,
            values={"cap": cap, "rate": rate},
        ))

    limit = policy.sublimit_for(ExpenseHead.INVESTIGATIONS)
    if limit and limit.amount:
        cap_text = format_inr(limit.amount)
        spent = format_inr(state.accrued_by_head().get(ExpenseHead.INVESTIGATIONS, ZERO))
        items.insert(0, ChecklistItem(
            "diagnostics_sublimit",
            f"Tell the doctor your policy caps tests at {cap_text}",
            f"Used so far: {spent}. Anything above the cap is yours to pay.",
            urgent=True,
            values={"cap": cap_text, "spent": spent},
        ))

    if procedure is not None and procedure.requires_implant:
        items.append(ChecklistItem(
            "implant_invoice",
            "Ask for the implant invoice and its sticker",
            "Implants are claimed separately and refused without the maker's "
            "invoice. There is no way to get it later.",
            urgent=True,
        ))

    if not policy.covers_consumables:
        items.append(ChecklistItem(
            "consumables_running",
            "Ask the ward to itemise the consumables",
            "You are paying for these, so a list is the only way to check them "
            "at discharge.",
        ))

    if not state.pre_auth_filed:
        items.insert(0, ChecklistItem(
            "chase_preauth",
            "Chase the pre-authorisation at the insurance desk, by name",
            "An unread request is the commonest reason cashless turns into "
            "cash. Ask how much was approved, not only whether: insurers often "
            "approve less, and the gap is yours.",
            urgent=True,
        ))

    return items


def _discharge_planning(
    state: JourneyState,
    policy: NormalizedPolicy,
    settlement: SettlementMode | None,
    procedure: Procedure | None,
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
            "No claim is paid without it. Check it names the treatment and "
            "both dates.",
            urgent=True,
            tags=["paperwork"],
        ),
        ChecklistItem(
            "itemised_bill",
            "Collect the itemised bill, not the one-line total",
            "One figure cannot be checked against your policy, and the insurer "
            "will query it.",
            urgent=True,
            tags=["paperwork"],
        ),
        ChecklistItem(
            "originals",
            "Collect original reports, prescriptions and receipts",
            "Originals, not copies. Claims are refused without them, and the "
            "hospital keeps no second set.",
            urgent=True,
            tags=["paperwork"],
        ),
        ChecklistItem(
            "check_non_payables",
            "Check the bill for items your insurer never pays",
            "Gloves, gowns and record charges are on the IRDAI non-payable "
            "list and belong on your side. Photograph the bill above and we "
            "will go through it line by line.",
            urgent=True,
        ),
    ]

    if state.room_rate_per_day and _room_cap(policy):
        items.append(ChecklistItem(
            "check_deduction",
            "Check how the proportionate cut was worked out",
            "It applies to the room, nursing, doctor, surgeon and theatre "
            "only. Since May 2024 it must not touch medicines, tests, implants "
            "or ICU. The bill check above works it out for you.",
            urgent=True,
        ))

    if policy.post_hospitalisation_days:
        days = str(policy.post_hospitalisation_days)
        why = (
            "Follow-up visits, medicines and tests in that window are "
            "claimable, and are most often lost to a thrown-away receipt."
        )
        if state.admitted_at:
            until = f"{(state.admitted_at.date() + timedelta(days=policy.post_hospitalisation_days)):%d %B}"
            items.append(ChecklistItem(
                "post_window",
                f"Keep every prescription and bill until {until}",
                why,
                key="post_window_until",
                values={"days": days, "until": until},
                tags=["paperwork"],
            ))
        else:
            items.append(ChecklistItem(
                "post_window",
                f"Keep every prescription and bill for {days} more days",
                why,
                values={"days": days},
                tags=["paperwork"],
            ))

    if settlement is SettlementMode.REIMBURSEMENT:
        items.append(ChecklistItem(
            "claim_deadline",
            "Ask your insurer the deadline for filing the claim",
            "Reimbursement has a window, often 15 to 30 days from discharge. "
            "A late claim is refused on the date alone.",
            urgent=True,
        ))
    else:
        items.append(ChecklistItem(
            "final_approval",
            "Wait for the final approval before signing the bill",
            "The last approval often differs from the pre-auth, and what you "
            "sign for is what you owe.",
        ))

    return items


def _settled(
    state: JourneyState,
    policy: NormalizedPolicy,
    settlement: SettlementMode | None,
    procedure: Procedure | None,
) -> list[ChecklistItem]:
    return [
        ChecklistItem(
            "settlement_letter",
            "Keep the settlement letter with the bills",
            "It states what was paid and what was cut, and any dispute is "
            "argued from it.",
        ),
        ChecklistItem(
            "check_deductions",
            "Check each deduction against your policy",
            "A cut that matches no clause in your own document is worth "
            "querying. Insurers do correct them.",
        ),
        ChecklistItem(
            "note_remaining",
            "Note what cover is left for this policy year",
            "Any admission before your renewal has to fit inside it.",
        ),
    ]


_BUILDERS = {
    JourneyStage.PRE_ADMISSION: _pre_admission,
    JourneyStage.ADMITTED: _admitted,
    JourneyStage.DISCHARGE_PLANNING: _discharge_planning,
    JourneyStage.SETTLED: _settled,
}


def _room_cap(policy: NormalizedPolicy) -> str:
    """The daily room entitlement in words, or nothing if there is no cap."""
    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    return format_inr(cap) if cap else ""
