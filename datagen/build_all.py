"""Build the full dataset and report on it.

Run from the repository root:

    python -m datagen.build_all          # everything, including the documents
    python -m datagen.build_all --core   # just what the running app reads

Validation runs as part of the build rather than as a separate optional step.
A corpus with a broken cost split or an unreachable procedure produces cost
estimates that look plausible and are wrong, which is the worst failure mode
this system has.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.core.config import GENERATED_DIR
from app.schemas.hospital import Hospital, HospitalType, Insurer
from app.schemas.money import format_inr
from app.schemas.policy import RoomCategory
from app.schemas.procedure import Procedure
from datagen.build_bills import build_bill_corpus
from datagen.build_policies import build_policy_corpus
from datagen.geo import CITIES
from datagen.hospitals import build_hospitals
from datagen.insurers import build_insurers
from datagen.procedures import build_procedures


def _write(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def validate(
    procedures: list[Procedure], hospitals: list[Hospital], insurers: list[Insurer]
) -> list[str]:
    """Return a list of problems. Empty means the corpus is coherent."""
    problems: list[str] = []
    codes = {p.code for p in procedures}

    if len(codes) != len(procedures):
        problems.append("duplicate procedure codes")

    for proc in procedures:
        total = sum(proc.cost_split.fractions.values())
        if abs(total - 1.0) > 0.005:
            problems.append(f"{proc.code}: cost split sums to {total:.4f}")
        if proc.base_rate_nabh <= proc.base_rate_non_nabh:
            problems.append(f"{proc.code}: NABH rate not above non-NABH")
        parts = proc.cost_split.apply(proc.base_rate_non_nabh)
        if sum(parts.values()) != proc.base_rate_non_nabh:
            problems.append(f"{proc.code}: split does not reconcile to the total")

    ids = {h.hospital_id for h in hospitals}
    if len(ids) != len(hospitals):
        problems.append("duplicate hospital ids")
    if len({h.name for h in hospitals}) != len(hospitals):
        problems.append("duplicate hospital names")

    insurer_ids = {i.insurer_id for i in insurers}
    for hospital in hospitals:
        if not hospital.room_tariffs:
            problems.append(f"{hospital.hospital_id}: no room tariffs")
        if unknown := set(hospital.procedure_codes) - codes:
            problems.append(f"{hospital.hospital_id}: unknown procedures {list(unknown)[:3]}")
        if unknown_ins := set(hospital.cashless_insurers) - insurer_ids:
            problems.append(f"{hospital.hospital_id}: unknown insurers {list(unknown_ins)}")

        # Room prices must rise with room tier, or downgrade advice inverts.
        ladder = [
            t for t in hospital.room_tariffs if t.category is not RoomCategory.ICU
        ]
        ladder.sort(key=lambda t: t.category.rank)
        rates = [t.per_day for t in ladder]
        if rates != sorted(rates):
            problems.append(f"{hospital.hospital_id}: room rates not monotonic")

    # Every procedure must be performable somewhere, or it can never be matched.
    offered = {code for h in hospitals for code in h.procedure_codes}
    if orphans := codes - offered:
        problems.append(f"{len(orphans)} procedures offered by no hospital")

    return problems


def report(
    procedures: list[Procedure], hospitals: list[Hospital], insurers: list[Insurer]
) -> str:
    lines: list[str] = []
    add = lines.append

    add("=" * 68)
    add("POLIMAP DATASET")
    add("=" * 68)
    add(f"procedures : {len(procedures)}")
    add(f"hospitals  : {len(hospitals)}")
    add(f"insurers   : {len(insurers)} "
        f"({sum(1 for i in insurers if i.is_government_scheme)} government schemes)")
    add("")

    add("-- hospitals by city " + "-" * 47)
    for city in CITIES:
        subset = [h for h in hospitals if h.city == city.name]
        accredited = sum(1 for h in subset if h.quality.accreditation.is_nabh_tier)
        beds = sum(h.quality.bed_count for h in subset)
        add(
            f"  {city.name:<12} {len(subset):>4} hospitals  "
            f"{accredited:>3} NABH/JCI  {beds:>6,} beds"
        )
    add("")

    add("-- composition " + "-" * 52)
    for label, counter in (
        ("type", Counter(h.hospital_type.value for h in hospitals)),
        ("accreditation", Counter(h.quality.accreditation.value for h in hospitals)),
    ):
        add(f"  {label}:")
        for key, count in counter.most_common():
            add(f"    {key:<22} {count:>4}  ({count / len(hospitals):>5.1%})")
    add("")

    add("-- room tariffs, private hospitals " + "-" * 33)
    private = [h for h in hospitals if h.hospital_type is HospitalType.PRIVATE]
    for category in (
        RoomCategory.GENERAL_WARD,
        RoomCategory.TWIN_SHARING,
        RoomCategory.SINGLE_PRIVATE,
        RoomCategory.DELUXE,
        RoomCategory.ICU,
    ):
        rates = sorted(t.per_day for h in private if (t := h.tariff_for(category)))
        if not rates:
            continue
        add(
            f"  {category.label:<20} min {format_inr(rates[0]):>9}"
            f"   median {format_inr(rates[len(rates) // 2]):>9}"
            f"   max {format_inr(rates[-1]):>10}"
        )
    add("")

    add("-- public vs private, general ward " + "-" * 33)
    for label, subset in (
        ("private", private),
        ("government", [h for h in hospitals if h.hospital_type is HospitalType.GOVERNMENT]),
    ):
        rates = sorted(
            t.per_day for h in subset if (t := h.tariff_for(RoomCategory.GENERAL_WARD))
        )
        if rates:
            add(f"  {label:<12} median {format_inr(rates[len(rates) // 2])}")
    add("")

    add("-- cashless network reach " + "-" * 42)
    commercial = [i for i in insurers if not i.is_government_scheme]
    for insurer in commercial:
        count = sum(1 for h in hospitals if insurer.insurer_id in h.cashless_insurers)
        add(f"  {insurer.short_name:<16} {count:>4} hospitals  ({count / len(hospitals):>5.1%})")
    add("")

    in_no_network = sum(1 for h in hospitals if not h.cashless_insurers)
    add(f"  hospitals in no cashless network: {in_no_network} "
        f"({in_no_network / len(hospitals):.1%})")
    add("")

    add("-- procedure catalogue " + "-" * 45)
    by_specialty = Counter(p.specialty.value for p in procedures)
    add(f"  {len(by_specialty)} specialties covered")
    add(f"  {sum(1 for p in procedures if p.requires_implant)} involve implants")
    add(f"  {sum(1 for p in procedures if p.is_daycare)} are daycare")
    rates = sorted(p.base_rate_non_nabh for p in procedures)
    add(f"  package rates: {format_inr(rates[0])} to {format_inr(rates[-1])}"
        f"  (median {format_inr(rates[len(rates) // 2])})")
    add("")

    return "\n".join(lines)


def _policy_report(manifest: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    policies = manifest["policies"]

    add("-- policy corpus " + "-" * 50)
    add(f"  {manifest['policy_count']} policies, "
        f"{manifest['document_count']} documents")

    by_condition = Counter(
        d["condition"] for p in policies for d in p["documents"]
    )
    add("  document conditions:")
    for condition, count in by_condition.most_common():
        add(f"    {condition:<16} {count:>3}")

    scanned = sum(
        1 for p in policies for d in p["documents"] if not d["has_text_layer"]
    )
    add(f"  without a text layer: {scanned} "
        f"({scanned / manifest['document_count']:.0%}), OCR required")

    add("  variation exercised:")
    add(f"    room limit phrasings : {dict(Counter(p['room_basis'] for p in policies))}")
    add(f"    amount styles        : {dict(Counter(p['amount_style'] for p in policies))}")
    add(f"    schedule contradicts wording : "
        f"{sum(1 for p in policies if p['contradicts_wording'])}")
    add(f"    top-up plans (deductible)    : "
        f"{sum(1 for p in policies if p['is_top_up'])}")
    add("")
    return "\n".join(lines)


def _bill_report(manifest: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append

    add("-- bill corpus " + "-" * 52)
    add(f"  {manifest['bill_count']} bills, {manifest['document_count']} documents")
    add(f"  carrying no planted fault: {manifest['clean_bills']}")
    add("  faults planted:")
    for fault in manifest["faults"]:
        count = sum(1 for b in manifest["bills"] if fault in b["planted"])
        add(f"    {fault:<18} {count:>3}")
    add("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--core",
        action="store_true",
        help=(
            "Build only the data the running application needs: procedures, "
            "hospitals and insurers. Skips rendering the policy documents, "
            "which take most of the time and all of the disk, and which only "
            "the tests and benchmarks read."
        ),
    )
    args = parser.parse_args(argv)

    procedures = build_procedures()
    insurers = build_insurers()
    hospitals = build_hospitals(procedures)

    problems = validate(procedures, hospitals, insurers)

    print(report(procedures, hospitals, insurers))

    if args.core:
        print("core build: skipping the policy document corpus")
        print()
    else:
        print("building policy corpus (rendering and degrading documents)...")
        manifest = build_policy_corpus()
        print()
        print(_policy_report(manifest))

        print("building bill corpus...")
        bills = build_bill_corpus(hospitals, procedures)
        print()
        print(_bill_report(bills))

    if problems:
        print("-- VALIDATION FAILED " + "-" * 46)
        for problem in problems[:25]:
            print(f"  ! {problem}")
        if len(problems) > 25:
            print(f"  ... and {len(problems) - 25} more")
        return 1

    paths = [
        _write(
            GENERATED_DIR / "procedures.json",
            [p.model_dump(mode="json") for p in procedures],
        ),
        _write(
            GENERATED_DIR / "hospitals.json",
            [h.model_dump(mode="json") for h in hospitals],
        ),
        _write(
            GENERATED_DIR / "insurers.json",
            [i.model_dump(mode="json") for i in insurers],
        ),
    ]

    print("-- validation passed " + "-" * 46)
    for path in paths:
        size_kb = path.stat().st_size / 1024
        print(f"  wrote {path.relative_to(GENERATED_DIR.parent.parent)}  ({size_kb:,.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())