"""Insurers and government schemes.

All insurer names are invented. Using real company names would attach fabricated
network data, tariffs and claim behaviour to identifiable businesses, which is
both unfair and misleading; the problem statement asks for synthetic insurance
data in any case.

Government schemes are modelled as insurers too, because from the user's side
they answer the same questions, where am I covered, what will I pay, even
though they settle on fixed package rates rather than against a bill.
"""

from __future__ import annotations

from app.schemas.hospital import GovernmentScheme, Insurer

# Invented insurers. `network_reach` is the share of eligible private hospitals
# this insurer has a cashless tie-up with, before quality weighting.
PRIVATE_INSURERS: list[tuple[str, str, str, float]] = [
    ("INS_SENTINEL", "Sentinel Health Insurance", "Sentinel", 0.62),
    ("INS_PRAYAAN", "Prayaan General Insurance", "Prayaan", 0.55),
    ("INS_SURAKSHA", "Suraksha First Health", "Suraksha First", 0.48),
    ("INS_MEDITRUST", "MediTrust Insurance", "MediTrust", 0.70),
    ("INS_ANVAYA", "Anvaya Health Assurance", "Anvaya", 0.40),
    ("INS_BHARATCARE", "BharatCare General Insurance", "BharatCare", 0.66),
    ("INS_NIVARAN", "Nivaran Health Insurance", "Nivaran", 0.35),
    ("INS_KAVACH", "Kavach Assurance", "Kavach", 0.52),
    ("INS_SWASTHYAONE", "SwasthyaOne Insurance", "SwasthyaOne", 0.44),
    ("INS_AEGISBHARAT", "Aegis Bharat Health", "Aegis Bharat", 0.58),
]

SCHEME_INSURERS: list[tuple[str, GovernmentScheme]] = [
    ("SCH_PMJAY", GovernmentScheme.PMJAY),
    ("SCH_CGHS", GovernmentScheme.CGHS),
    ("SCH_ESI", GovernmentScheme.ESI),
    ("SCH_AROGYA_KARNATAKA", GovernmentScheme.AROGYA_KARNATAKA),
    ("SCH_YESHASWINI", GovernmentScheme.YESHASWINI),
    ("SCH_MJPJAY", GovernmentScheme.MJPJAY),
    ("SCH_AAROGYASRI", GovernmentScheme.AAROGYASRI),
    ("SCH_DELHI_AAROGYA_KOSH", GovernmentScheme.DELHI_AAROGYA_KOSH),
]

NETWORK_REACH: dict[str, float] = {i[0]: i[3] for i in PRIVATE_INSURERS}


def build_insurers() -> list[Insurer]:
    insurers = [
        Insurer(insurer_id=iid, name=name, short_name=short)
        for iid, name, short, _ in PRIVATE_INSURERS
    ]
    insurers.extend(
        Insurer(
            insurer_id=iid,
            name=scheme.label,
            short_name=scheme.label,
            is_government_scheme=True,
        )
        for iid, scheme in SCHEME_INSURERS
    )
    return insurers


SCHEME_TO_INSURER_ID: dict[GovernmentScheme, str] = {
    scheme: iid for iid, scheme in SCHEME_INSURERS
}
