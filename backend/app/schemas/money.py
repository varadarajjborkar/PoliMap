"""Rupee arithmetic.

Every figure this system shows a user is money, and the deduction waterfall
chains percentages (co-pay, proportionate deduction) across several steps.
Binary floats accumulate error through that chain and produce totals that fail
to reconcile against their own line items, so all monetary values are `Decimal`
and every step rounds explicitly.

Rounding is half-up to whole rupees, matching how Indian insurers settle
claims. Sub-rupee precision is not meaningful here and carrying it makes
line items fail to sum to their stated total.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer

ZERO = Decimal("0")
RUPEE = Decimal("1")


def to_decimal(value: Any) -> Decimal:
    """Coerce user, model, or dataset input into an exact Decimal."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("boolean is not a monetary value")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # Via str, so 0.1 becomes Decimal("0.1") and not the binary artefact.
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = (
            value.strip()
            .replace("₹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace("INR", "")
            .replace(",", "")
            .replace("/-", "")
            .strip()
        )
        if not cleaned:
            raise ValueError("empty monetary value")
        try:
            return Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"not a monetary value: {value!r}") from exc
    raise ValueError(f"not a monetary value: {value!r}")


def round_inr(value: Decimal) -> Decimal:
    """Round to whole rupees, half-up."""
    return value.quantize(RUPEE, rounding=ROUND_HALF_UP)


def _validate_rupees(value: Any) -> Decimal:
    return round_inr(to_decimal(value))


Rupees = Annotated[
    Decimal,
    BeforeValidator(_validate_rupees),
    # Serialize as a JSON number so the frontend does no parsing.
    PlainSerializer(lambda d: float(d), return_type=float, when_used="json"),
]
"""A whole-rupee amount. Rounds on construction so stored values are settled."""


Ratio = Annotated[
    Decimal,
    BeforeValidator(to_decimal),
    PlainSerializer(lambda d: float(d), return_type=float, when_used="json"),
]
"""An unrounded proportion, e.g. a 0.625 proportionate-deduction factor."""


def apply_pct(amount: Decimal, pct: Decimal) -> Decimal:
    """`pct` percent of `amount`, rounded to rupees. `pct` is 0-100."""
    return round_inr(amount * pct / Decimal(100))


def apply_ratio(amount: Decimal, ratio: Decimal) -> Decimal:
    """`ratio` fraction of `amount`, rounded to rupees. `ratio` is 0-1."""
    return round_inr(amount * ratio)


def format_inr(value: Decimal | int | float) -> str:
    """Format in the Indian grouping convention: 12,34,567."""
    amount = round_inr(to_decimal(value))
    negative = amount < 0
    digits = str(abs(amount).to_integral_value())

    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        grouped = ",".join([*parts, tail])
    else:
        grouped = digits

    return f"{'-' if negative else ''}₹{grouped}"


def format_inr_compact(value: Decimal | int | float) -> str:
    """Short form using Indian scale words, for dense UI surfaces."""
    amount = round_inr(to_decimal(value))
    magnitude = abs(amount)
    sign = "-" if amount < 0 else ""

    if magnitude >= Decimal("10000000"):
        return f"{sign}₹{_trim(magnitude / Decimal('10000000'))} Cr"
    if magnitude >= Decimal("100000"):
        return f"{sign}₹{_trim(magnitude / Decimal('100000'))} L"
    if magnitude >= Decimal("1000"):
        return f"{sign}₹{_trim(magnitude / Decimal('1000'))}K"
    return format_inr(amount)


def _trim(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).normalize()
    return format(rounded, "f")
