"""Intake benchmark: how much of a document survives each capture condition.

Two things are measured, and the second matters far more than the first.

*Token recall* is the share of the original words that came back. It is a broad
health check, and a page can score well on it while having mangled the one line
that decides a claim.

*Field recall* asks whether the specific figures the system depends on (sum
insured, room rent limit, co-payment, policy number) are present and exactly
right in the recovered text. A pipeline cannot extract what OCR never produced,
so this number is the ceiling on end-to-end accuracy, and it is the number to
optimise.

Ground truth for a document is its own clean render, so this isolates capture
damage from generation randomness.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz

from app.core.config import GENERATED_DIR
from app.pipeline.s0_intake import intake
from bench import REPORTS_DIR
from datagen.build_policies import load_manifest

_WORD_RE = re.compile(r"[A-Za-z0-9₹%/.,-]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


def normalise_figure(text: str) -> str:
    """Collapse a rupee figure to comparable digits."""
    return re.sub(r"[^0-9]", "", text)


@dataclass
class FieldProbe:
    """One figure that must survive capture, and how to look for it."""

    name: str
    variants: list[str]
    """Any one of these appearing in the text counts as recovered."""

    def found_in(self, haystack: str) -> bool:
        packed = re.sub(r"\s+", "", haystack.lower())
        return any(
            re.sub(r"\s+", "", v.lower()) in packed for v in self.variants if v
        )


def probes_for(truth: dict[str, Any], blueprint: dict[str, Any]) -> list[FieldProbe]:
    """Build the checks for one policy from its ground truth."""
    probes: list[FieldProbe] = []

    sum_insured = int(truth["sum_insured"])
    probes.append(FieldProbe("sum_insured", _amount_variants(sum_insured)))

    room = truth["room_limit"]
    if room.get("amount_per_day"):
        probes.append(
            FieldProbe("room_rent_cap", _amount_variants(int(room["amount_per_day"])))
        )
    elif room.get("pct_of_si"):
        pct = float(room["pct_of_si"])
        probes.append(
            FieldProbe("room_rent_pct", [f"{pct:g}%of sum insured", f"{pct:g}%"])
        )

    if float(truth.get("copay_pct") or 0) > 0:
        pct = float(truth["copay_pct"])
        probes.append(FieldProbe("copay", [f"{pct:g}%"]))

    probes.append(FieldProbe("policy_number", [blueprint["policy_number"]]))
    probes.append(FieldProbe("policyholder", [blueprint["policyholder"]]))

    for entry in truth.get("sublimits", []):
        if entry.get("amount"):
            probes.append(
                FieldProbe(
                    f"sublimit:{entry.get('label') or entry.get('head')}",
                    _amount_variants(int(entry["amount"])),
                )
            )
    return probes


def _amount_variants(value: int) -> list[str]:
    """Every way this figure might legitimately appear in recovered text.

    Must cover all the styles the generator emits. A probe that only knows the
    grouped-digit form reports a miss on a document that spelled the figure
    correctly in lakhs, which understates recall and sends optimisation effort
    at a problem that does not exist.
    """
    from app.schemas.money import format_inr

    grouped = format_inr(value)[1:]
    variants = [grouped, f"₹{grouped}", f"rs.{grouped}", str(value)]

    if value >= 100000:
        variants.append(f"{value / 100000:.2f}lakhs")
        variants.append(f"rs.{value / 100000:.2f}lakhs")
    if value >= 10000000:
        variants.append(f"{value / 10000000:.2f}crore")
    return variants


@dataclass
class DocResult:
    policy_id: str
    condition: str
    kind: str
    path: str
    chars: int = 0
    quality: float = 0.0
    token_recall: float = 0.0
    fields_found: int = 0
    fields_total: int = 0
    missing_fields: list[str] = field(default_factory=list)
    source_modes: list[str] = field(default_factory=list)
    escalated: bool = False
    seconds: float = 0.0
    error: str = ""

    @property
    def field_recall(self) -> float:
        return self.fields_found / self.fields_total if self.fields_total else 0.0


def reference_text(clean_pdf: Path) -> str:
    with fitz.open(clean_pdf) as doc:
        return "\n".join(page.get_text() for page in doc)


def evaluate_document(
    doc_entry: dict[str, Any],
    policy_entry: dict[str, Any],
    reference: str,
    probes: list[FieldProbe],
) -> DocResult:
    path = GENERATED_DIR / doc_entry["path"]
    result = DocResult(
        policy_id=policy_entry["policy_id"],
        condition=doc_entry["condition"],
        kind=doc_entry["kind"],
        path=doc_entry["path"],
        fields_total=len(probes),
    )

    started = time.perf_counter()
    try:
        document = intake.ingest(path, session_id="bench", save_page_images=False)
    except Exception as exc:
        result.error = f"{type(exc).__name__}: {exc}"[:160]
        result.seconds = time.perf_counter() - started
        return result
    result.seconds = time.perf_counter() - started

    recovered = document.full_text()
    result.chars = document.total_chars
    result.quality = document.quality_score
    result.source_modes = sorted({p.source_mode.value for p in document.pages})
    result.escalated = any(p.escalated for p in document.pages)

    # A health card carries only a few fields, so it is scored against the
    # subset it can possibly contain rather than the whole schedule.
    applicable = probes
    if doc_entry["kind"] == "card":
        applicable = [
            p for p in probes
            if p.name in {"sum_insured", "room_rent_cap", "room_rent_pct",
                          "policy_number", "policyholder"}
        ]
        result.fields_total = len(applicable)

    found = [p for p in applicable if p.found_in(recovered)]
    result.fields_found = len(found)
    result.missing_fields = [p.name for p in applicable if p not in found]

    reference_tokens = tokenize(reference)
    recovered_counts: dict[str, int] = defaultdict(int)
    for token in tokenize(recovered):
        recovered_counts[token] += 1

    matched = 0
    for token in reference_tokens:
        if recovered_counts[token] > 0:
            recovered_counts[token] -= 1
            matched += 1
    result.token_recall = round(matched / len(reference_tokens), 4) if reference_tokens else 0.0
    return result


def run(limit: int | None = None, conditions: set[str] | None = None) -> list[DocResult]:
    manifest = load_manifest()
    policies = manifest["policies"]
    if limit:
        policies = policies[:limit]

    results: list[DocResult] = []
    for policy in policies:
        truth_blob = json.loads(
            (GENERATED_DIR / policy["truth_path"]).read_text(encoding="utf-8")
        )
        probes = probes_for(truth_blob["truth"], truth_blob["blueprint"])

        clean = next(
            (d for d in policy["documents"] if d["condition"] == "native_pdf"
             and d["kind"] == "policy"),
            None,
        )
        if clean is None:
            continue
        reference = reference_text(GENERATED_DIR / clean["path"])

        for doc_entry in policy["documents"]:
            if conditions and doc_entry["condition"] not in conditions:
                continue
            results.append(evaluate_document(doc_entry, policy, reference, probes))

    return results


def report(results: list[DocResult]) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Intake benchmark")
    add("")
    add(f"{len(results)} documents evaluated.")
    add("")

    by_condition: dict[str, list[DocResult]] = defaultdict(list)
    for r in results:
        by_condition[r.condition].append(r)

    add("## By document condition")
    add("")
    add("| Condition | Docs | Field recall | Token recall | Quality | Escalated | Mean time |")
    add("|---|---:|---:|---:|---:|---:|---:|")

    order = ["native_pdf", "clean_scan", "skewed_scan", "photocopy", "phone_photo",
             "dark_photo"]
    for condition in sorted(by_condition, key=lambda c: order.index(c) if c in order else 99):
        group = by_condition[condition]
        n = len(group)
        add(
            f"| {condition} | {n} | "
            f"{sum(r.field_recall for r in group) / n:.1%} | "
            f"{sum(r.token_recall for r in group) / n:.1%} | "
            f"{sum(r.quality for r in group) / n:.2f} | "
            f"{sum(r.escalated for r in group)} | "
            f"{sum(r.seconds for r in group) / n:.1f}s |"
        )
    add("")

    total_found = sum(r.fields_found for r in results)
    total_fields = sum(r.fields_total for r in results)
    add(f"**Overall field recall: {total_found}/{total_fields} "
        f"({total_found / total_fields:.1%})**")
    add("")

    missing: dict[str, int] = defaultdict(int)
    for r in results:
        for name in r.missing_fields:
            missing[name.split(":")[0]] += 1
    if missing:
        add("## Fields most often lost")
        add("")
        add("| Field | Times missing |")
        add("|---|---:|")
        for name, count in sorted(missing.items(), key=lambda kv: -kv[1])[:12]:
            add(f"| {name} | {count} |")
        add("")

    failures = [r for r in results if r.error]
    if failures:
        add("## Errors")
        add("")
        for r in failures[:10]:
            add(f"- `{r.path}`: {r.error}")
        add("")

    worst = sorted(
        (r for r in results if not r.error and r.condition != "native_pdf"),
        key=lambda r: r.field_recall,
    )[:8]
    if worst:
        add("## Hardest documents")
        add("")
        add("| Document | Condition | Field recall | Missing |")
        add("|---|---|---:|---|")
        for r in worst:
            add(f"| {r.policy_id} | {r.condition} | {r.field_recall:.0%} | "
                f"{', '.join(r.missing_fields[:3]) or '-'} |")
        add("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark document intake.")
    parser.add_argument("--limit", type=int, help="only the first N policies")
    parser.add_argument("--condition", action="append", help="restrict to a condition")
    args = parser.parse_args()

    started = time.perf_counter()
    results = run(limit=args.limit, conditions=set(args.condition) if args.condition else None)
    text = report(results)
    print(text)
    print(f"\ncompleted in {time.perf_counter() - started:.0f}s")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "ocr_bench.md"
    out.write_text(text, encoding="utf-8")
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
