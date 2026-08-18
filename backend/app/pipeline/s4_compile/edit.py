"""Correcting a field the system read wrong.

Machines misread documents. When they do, the user is looking straight at the
mistake on their own screen, next to the figure they know to be right, and until
now there was nothing they could do about it. Everything downstream is computed
from these few numbers, so one misread digit quietly poisons every estimate
after it, and the user watched it happen.

Edits go through the same interpreter the clarification answers use, so "5 lakh"
is as acceptable here as 500000. What an edit cannot do is introduce a field:
the set below is closed, and a value is only ever applied to the field named by
the control that was clicked.

An edited field is marked as the user's own. That is a stronger claim than
anything extracted, so it outranks the clause it replaces and is never asked
about again.
"""

from __future__ import annotations

from decimal import Decimal

from app.pipeline.s4_compile.interpret import interpret, parse_amount, parse_percent
from app.schemas.money import format_inr
from app.schemas.policy import (
    ClauseStatus,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
)


class NotEditable(ValueError):
    """A field the interface may not write to."""


class Unreadable(ValueError):
    """A value we could not turn into a figure, reported back in plain words."""


# Closed on purpose. An open set would let a mistyped field name create a
# second, wrong field beside the real one, which is the same failure the
# clarification loop is built to avoid.
EDITABLE: dict[str, str] = {
    "sum_insured": "amount",
    "sum_insured_remaining": "amount",
    "room_limit": "amount",
    "copay_pct": "percent",
    "deductible": "amount",
    "covers_consumables": "boolean",
    "pre_hospitalisation_days": "days",
    "post_hospitalisation_days": "days",
}

LABELS: dict[str, str] = {
    "sum_insured": "Total cover this year",
    "sum_insured_remaining": "Cover left this year",
    "room_limit": "Room rent limit",
    "copay_pct": "Your share of every claim",
    "deductible": "The amount you pay first",
    "covers_consumables": "Consumables cover",
    "pre_hospitalisation_days": "Days covered before admission",
    "post_hospitalisation_days": "Days covered after discharge",
}


def _amount(value: object, label: str, *, allow_zero: bool = False) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    text = str(value).strip()
    # Zero is a real answer for a deductible or a co-payment, and `parse_amount`
    # rejects it deliberately: a cover of zero is a misreading, not a policy.
    # So the caller says whether zero means something for this field.
    if allow_zero and text.replace(",", "").strip() in ("0", "0.0", ""):
        return Decimal(0)

    parsed = parse_amount(text)
    if parsed is None:
        reading = interpret(label, str(value), expects="amount")
        if reading.best and reading.best.value is not None:
            return reading.best.value
        raise Unreadable(
            "We could not read that as an amount. Try 500000, or 5 lakh."
        )
    return parsed


def _percent(value: object, label: str) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    text = str(value).strip()
    # "None" and "0" are the same answer here, and the commonest one.
    if text.replace(",", "").lower() in ("0", "0%", "none", "nil", ""):
        return Decimal(0)

    parsed = parse_percent(text)
    if parsed is None:
        parsed = parse_amount(text)
    if parsed is None:
        raise Unreadable("We could not read that as a percentage. Try 10, or 10%.")
    return parsed


def edit_field(
    policy: NormalizedPolicy, field: str, value: object
) -> NormalizedPolicy:
    """Apply a correction the user made to a field they can see."""
    if field not in EDITABLE:
        raise NotEditable(field)

    label = LABELS.get(field, field)

    if field == "sum_insured":
        policy.sum_insured = _amount(value, label)
    elif field == "sum_insured_remaining":
        # A claim earlier in the policy year is the commonest reason an estimate
        # is wrong, and no document can know about it: the schedule states the
        # cover bought, not the cover left. Nothing was setting this, so every
        # estimate silently assumed a year with no claims in it.
        remaining = _amount(value, label, allow_zero=True)
        if remaining > policy.sum_insured:
            raise Unreadable(
                f"That is more than your total cover of "
                f"{format_inr(policy.sum_insured)}."
            )
        policy.sum_insured_remaining = remaining
    elif field == "copay_pct":
        policy.copay_pct = _percent(value, label)
    elif field == "deductible":
        policy.deductible = _amount(value, label, allow_zero=True)
    elif field == "covers_consumables":
        policy.covers_consumables = bool(value)
    elif field in ("pre_hospitalisation_days", "post_hospitalisation_days"):
        try:
            setattr(policy, field, max(int(str(value).strip() or 0), 0))
        except ValueError as exc:
            raise Unreadable("Enter a number of days.") from exc
    elif field == "room_limit":
        policy.room_limit = _room_limit(value, label)

    _mark_user_edited(policy, field)
    return policy


def _room_limit(value: object, label: str) -> RoomLimit:
    """Read the several shapes a room entitlement comes in.

    A room limit is not one number. It is a rupee cap, or a percentage of the
    cover, or a room category, or nothing at all, and a policy can state two of
    them at once. An edit box that only accepted rupees would force the other
    three into a shape the policy never had.
    """
    text = str(value).strip()
    if not text:
        return RoomLimit(basis=RoomLimitBasis.NO_LIMIT)

    lowered = text.lower()
    if lowered in ("none", "no limit", "no cap", "unlimited", "0"):
        return RoomLimit(basis=RoomLimitBasis.NO_LIMIT)

    for category in RoomCategory:
        if category.value in lowered.replace(" ", "_") or (
            category.label.lower() in lowered
        ):
            return RoomLimit(
                basis=RoomLimitBasis.CATEGORY_ONLY, category_ceiling=category
            )

    if "%" in text or "percent" in lowered or "per cent" in lowered:
        pct = parse_percent(text)
        if pct is None:
            raise Unreadable("We could not read that percentage. Try 1%.")
        return RoomLimit(basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=pct)

    return RoomLimit(
        basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=_amount(text, label)
    )


# Which clause kinds a field settles, so the ledger agrees with the correction.
_FIELD_CLAUSES: dict[str, tuple[str, ...]] = {
    "sum_insured": ("sum_insured",),
    "room_limit": ("room_rent_cap", "room_category_eligibility"),
    "copay_pct": ("copay",),
    "deductible": ("deductible",),
    "covers_consumables": ("consumables_cover",),
}


def _mark_user_edited(policy: NormalizedPolicy, field: str) -> None:
    """Record that this is the user's own figure, not something we read.

    A correction is a stronger claim than any extraction, so the clause it
    replaces is settled rather than left open. Without this the system would
    keep asking about a value the user has already told it.
    """
    kinds = _FIELD_CLAUSES.get(field, ())
    for clause in policy.clauses:
        if clause.kind.value in kinds:
            clause.status = ClauseStatus.CONFIRMED
            if "Corrected by you." not in clause.notes:
                clause.notes.append("Corrected by you.")

    policy.open_clarifications = [
        request for request in policy.open_clarifications
        if request.clause_kind.value not in kinds
    ]
