"""How a government scheme settles, which is not how a policy settles.

A commercial indemnity policy reimburses against an itemised bill: it tests each
head against a cap, reduces what is priced by room tier, takes the
policyholder's share, and pays the remainder. Every mechanism in the deduction
waterfall exists because a bill is the unit of settlement.

A public scheme does none of that. Treatment is bought at a fixed, all-inclusive
package rate set by the scheme, at a hospital empanelled to accept it. The
package covers consumables, implants, drugs, diagnostics and food, so the heads
an indemnity policy strips out are the very heads a scheme includes. There is a
ward entitlement rather than a rupee room cap, no co-payment, and nothing to
claim back afterwards.

Running one model over the other is not a rounding error. It tells a PM-JAY
family that gloves and syringes are theirs to pay, and that they should arrange
a lakh in cash and claim it back later. Both are false, and both are false in
the direction that frightens the poorest user this system has. So the scheme
rules live here, separately, and the simulator dispatches on them.

Figures are the published design of each scheme, not a claim about any
individual's entitlement: the cover ceilings and the general-ward entitlement
are matters of public record, while the package rates in the corpus remain
synthetic and CGHS-anchored like everything else here.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.hospital import GovernmentScheme
from app.schemas.money import Rupees
from app.schemas.policy import RoomCategory


class SchemeRules(BaseModel):
    """What one scheme pays for, and on what terms."""

    scheme: GovernmentScheme
    cover_per_year: Rupees
    """The scheme ceiling. For a family scheme this is shared across the family,
    which is why it can be spent by a relative's admission earlier in the year."""

    family_floater: bool = True
    room_entitlement: RoomCategory = RoomCategory.GENERAL_WARD
    copay_pct: Decimal = Field(default=Decimal(0), ge=0, le=100)

    package_covers_everything: bool = True
    """Consumables, implants, drugs, diagnostics and food are inside the package
    price rather than billed on top of it."""

    pre_hospitalisation_days: int = 0
    post_hospitalisation_days: int = 0

    reimbursement_possible: bool = False
    """Whether a non-empanelled hospital can be used and claimed back. For the
    package schemes it cannot, and saying otherwise is the dangerous error."""

    package_rate_factor: Decimal = Decimal("1.00")
    """Scheme package price relative to the CGHS non-NABH rate the corpus is
    anchored on. The package schemes negotiate below CGHS; CGHS itself is 1.0."""

    note: str = ""

    @property
    def label(self) -> str:
        return self.scheme.label


# Cover ceilings and the general-ward entitlement follow each scheme's published
# design. The rate factors are the modelling assumption: package schemes settle
# meaningfully below CGHS, and that gap is the reason an empanelled hospital
# treats a scheme patient differently from a cash patient.
SCHEME_RULES: dict[GovernmentScheme, SchemeRules] = {
    GovernmentScheme.PMJAY: SchemeRules(
        scheme=GovernmentScheme.PMJAY,
        cover_per_year=Decimal("500000"),
        family_floater=True,
        pre_hospitalisation_days=3,
        post_hospitalisation_days=15,
        package_rate_factor=Decimal("0.62"),
        note=(
            "Treatment is free at an empanelled hospital, up to the family "
            "cover for the year. There is nothing to pay and nothing to claim "
            "back afterwards."
        ),
    ),
    GovernmentScheme.CGHS: SchemeRules(
        scheme=GovernmentScheme.CGHS,
        cover_per_year=Decimal("1000000"),
        family_floater=True,
        room_entitlement=RoomCategory.TWIN_SHARING,
        package_rate_factor=Decimal("1.00"),
        post_hospitalisation_days=10,
        reimbursement_possible=True,
        note=(
            "Ward entitlement follows your pay band, so the room you are "
            "eligible for may be higher than the general ward assumed here."
        ),
    ),
    GovernmentScheme.ESI: SchemeRules(
        scheme=GovernmentScheme.ESI,
        cover_per_year=Decimal("1000000"),
        family_floater=True,
        package_rate_factor=Decimal("0.70"),
        post_hospitalisation_days=10,
        note=(
            "Treatment at an ESI hospital or a tied-up hospital is free for "
            "an insured person and their family."
        ),
    ),
    GovernmentScheme.AROGYA_KARNATAKA: SchemeRules(
        scheme=GovernmentScheme.AROGYA_KARNATAKA,
        cover_per_year=Decimal("500000"),
        package_rate_factor=Decimal("0.60"),
        post_hospitalisation_days=10,
        note=(
            "Referral from a public hospital is normally needed except in an "
            "emergency."
        ),
    ),
    GovernmentScheme.YESHASWINI: SchemeRules(
        scheme=GovernmentScheme.YESHASWINI,
        cover_per_year=Decimal("500000"),
        package_rate_factor=Decimal("0.58"),
        note="Open to members of a co-operative society and their families.",
    ),
    GovernmentScheme.MJPJAY: SchemeRules(
        scheme=GovernmentScheme.MJPJAY,
        cover_per_year=Decimal("500000"),
        package_rate_factor=Decimal("0.62"),
        post_hospitalisation_days=10,
    ),
    GovernmentScheme.AAROGYASRI: SchemeRules(
        scheme=GovernmentScheme.AAROGYASRI,
        cover_per_year=Decimal("500000"),
        package_rate_factor=Decimal("0.60"),
        post_hospitalisation_days=10,
    ),
    GovernmentScheme.DELHI_AAROGYA_KOSH: SchemeRules(
        scheme=GovernmentScheme.DELHI_AAROGYA_KOSH,
        cover_per_year=Decimal("500000"),
        package_rate_factor=Decimal("0.65"),
    ),
}


def rules_for(scheme: GovernmentScheme | str | None) -> SchemeRules | None:
    """The rules for a scheme, or None when this is a commercial policy."""
    if scheme is None:
        return None
    try:
        return SCHEME_RULES[GovernmentScheme(scheme)]
    except (ValueError, KeyError):
        return None
