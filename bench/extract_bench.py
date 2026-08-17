"""Extraction benchmark: does the ledger contain the right answer?

Scored per clause kind against the generator's ground truth, and split by
document condition, so a regression can be located rather than merely detected.
The distinction that matters most is between two very different failures:

* a **miss** — the clause is absent, which is a recall problem, and the user
  simply gets asked;
* a **wrong value** — a clause is present and confidently incorrect, which is
  the dangerous case, because nobody is prompted to check it.

They are reported separately, and wrong values are the number to drive to zero
even at the cost of misses.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.core.config import GENERATED_DIR
from app.pipeline.run import run_policy_pipeline
from app.schemas.policy import Clause, ClauseKind
from bench import REPORTS_DIR
from datagen.build_policies import load_manifest

TRACKED_FIELDS = [
    "sum_insured", "room_limit", "icu_limit", "copay", "deductible",
    "pre_hospitalisation", "post_hospitalisation", "consumables",
]


class Outcome:
    CORRECT = "correct"
    WRONG = "wrong"
    MISSING = "missing"
    NOT_APPLICABLE = "n/a"


@dataclass
class FieldResult:
    field: str
    outcome: str
    expected: str = ""
    got: str = ""
    confidence: float = 0.0


@dataclass
class PolicyResult:
    policy_id: str
    condition: str
    clause_count: int = 0
    questions: int = 0
    seconds: float = 0.0
    fields: list[FieldResult] = field(default_factory=list)
    error: str = ""


def best_clause(clauses: list[Clause], kind: ClauseKind) -> Clause | None:
    """The clause a compiler would choose: highest precedence, then confidence.

    A preview of stage 4's resolution, kept here so extraction can be measured
    before the compiler exists and independently of its behaviour afterwards.
    """
    candidates = [c for c in clauses if c.kind is kind and c.is_admissible]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda c: (c.evidence.section.precedence, c.confidence),
    )


def _num(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _compare_amount(
    name: str, expected: Any, clause: Clause | None, key: str = "amount_inr"
) -> FieldResult:
    want = _num(expected)
    if want is None or want == 0:
        # Nothing to find; a clause claiming otherwise is a false positive.
        if clause is None:
            return FieldResult(name, Outcome.NOT_APPLICABLE)
        got = _num(clause.params.get(key))
        if got and got > 0:
            return FieldResult(name, Outcome.WRONG, "none", str(got), clause.confidence)
        return FieldResult(name, Outcome.NOT_APPLICABLE)

    if clause is None:
        return FieldResult(name, Outcome.MISSING, str(want))

    got = _num(clause.params.get(key))
    if got is None:
        return FieldResult(name, Outcome.MISSING, str(want), confidence=clause.confidence)
    outcome = Outcome.CORRECT if got == want else Outcome.WRONG
    return FieldResult(name, outcome, str(want), str(got), clause.confidence)


def _compare_room_limit(
    name: str, expected: dict[str, Any], sum_insured: Decimal, clauses: list[Clause]
) -> FieldResult:
    """Room limits are compared on the rupee cap they resolve to.

    Comparing the stated basis would penalise an extractor that read "1% of
    Rs. 5,00,000" as a flat Rs. 5,000 — a different description of the identical
    entitlement, and one that costs the user nothing.
    """
    from app.schemas.policy import RoomLimit, RoomLimitBasis

    kind = (
        ClauseKind.ROOM_RENT_CAP if name == "room_limit" else ClauseKind.ICU_CAP
    )
    clause = best_clause(clauses, kind)
    if clause is None and name == "room_limit":
        clause = best_clause(clauses, ClauseKind.ROOM_CATEGORY_ELIGIBILITY)

    want_limit = RoomLimit(
        basis=RoomLimitBasis(expected.get("basis", "no_limit")),
        amount_per_day=expected.get("amount_per_day"),
        pct_of_si=expected.get("pct_of_si"),
    )
    want_cap = want_limit.effective_daily_cap(sum_insured)

    if want_cap is None:
        if clause is None:
            return FieldResult(name, Outcome.NOT_APPLICABLE)
        # A category-only or unlimited policy: reporting a category is right.
        if clause.params.get("basis") in ("category", "no_limit"):
            return FieldResult(name, Outcome.CORRECT, "no cap",
                               clause.params.get("basis", ""), clause.confidence)
        return FieldResult(name, Outcome.WRONG, "no cap",
                           str(clause.params), clause.confidence)

    if clause is None:
        return FieldResult(name, Outcome.MISSING, str(want_cap))

    got_limit = RoomLimit(
        basis=RoomLimitBasis.NO_LIMIT,
        amount_per_day=clause.params.get("amount_inr"),
        pct_of_si=clause.params.get("pct_of_si"),
    )
    got_cap = got_limit.effective_daily_cap(sum_insured)
    if got_cap is None:
        return FieldResult(name, Outcome.MISSING, str(want_cap),
                           confidence=clause.confidence)

    outcome = Outcome.CORRECT if got_cap == want_cap else Outcome.WRONG
    return FieldResult(name, outcome, str(want_cap), str(got_cap), clause.confidence)


def evaluate(clauses: list[Clause], truth: dict[str, Any]) -> list[FieldResult]:
    sum_insured = _num(truth["sum_insured"]) or Decimal(0)
    results = [
        _compare_amount("sum_insured", truth["sum_insured"],
                        best_clause(clauses, ClauseKind.SUM_INSURED)),
        _compare_room_limit("room_limit", truth["room_limit"], sum_insured, clauses),
        _compare_room_limit("icu_limit", truth["icu_limit"], sum_insured, clauses),
        _compare_amount("copay", truth["copay_pct"],
                        best_clause(clauses, ClauseKind.COPAY), key="pct"),
        _compare_amount("deductible", truth["deductible"],
                        best_clause(clauses, ClauseKind.DEDUCTIBLE)),
    ]

    for name, kind, key in (
        ("pre_hospitalisation", ClauseKind.PRE_HOSPITALISATION, "days"),
        ("post_hospitalisation", ClauseKind.POST_HOSPITALISATION, "days"),
    ):
        results.append(
            _compare_amount(
                name, truth[f"{name}_days"], best_clause(clauses, kind), key=key
            )
        )

    clause = best_clause(clauses, ClauseKind.CONSUMABLES_COVER)
    want = bool(truth["covers_consumables"])
    if clause is None:
        results.append(FieldResult("consumables", Outcome.MISSING, str(want)))
    else:
        got = bool(clause.params.get("covered"))
        results.append(
            FieldResult(
                "consumables",
                Outcome.CORRECT if got == want else Outcome.WRONG,
                str(want), str(got), clause.confidence,
            )
        )
    return results


def run(
    limit: int | None = None,
    conditions: set[str] | None = None,
    *,
    use_model: bool = True,
    verify_clauses: bool = True,
) -> list[PolicyResult]:
    manifest = load_manifest()
    policies = manifest["policies"][: limit or None]
    results: list[PolicyResult] = []

    for policy in policies:
        truth = json.loads(
            (GENERATED_DIR / policy["truth_path"]).read_text(encoding="utf-8")
        )["truth"]

        for doc_entry in policy["documents"]:
            if doc_entry["kind"] == "card":
                continue  # A card cannot carry most of the tracked fields.
            if conditions and doc_entry["condition"] not in conditions:
                continue

            result = PolicyResult(
                policy_id=policy["policy_id"], condition=doc_entry["condition"]
            )
            started = time.perf_counter()
            try:
                outcome = run_policy_pipeline(
                    GENERATED_DIR / doc_entry["path"],
                    session_id="bench",
                    use_model=use_model,
                    verify_clauses=verify_clauses,
                )
                clauses = outcome.verification.surviving
                result.clause_count = len(clauses)
                result.questions = len(outcome.policy.open_clarifications)
                result.fields = evaluate(clauses, truth)
            except Exception as exc:
                result.error = f"{type(exc).__name__}: {exc}"[:160]
            result.seconds = time.perf_counter() - started
            results.append(result)

    return results


def report(results: list[PolicyResult]) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Extraction benchmark")
    add("")
    add(f"{len(results)} documents.")
    add("")

    def tally(subset: list[FieldResult]) -> tuple[int, int, int, int]:
        scored = [f for f in subset if f.outcome != Outcome.NOT_APPLICABLE]
        correct = sum(1 for f in scored if f.outcome == Outcome.CORRECT)
        wrong = sum(1 for f in scored if f.outcome == Outcome.WRONG)
        missing = sum(1 for f in scored if f.outcome == Outcome.MISSING)
        return correct, wrong, missing, len(scored)

    add("## By field")
    add("")
    add("| Field | Correct | Wrong | Missing | Accuracy |")
    add("|---|---:|---:|---:|---:|")
    by_field: dict[str, list[FieldResult]] = defaultdict(list)
    for r in results:
        for f in r.fields:
            by_field[f.field].append(f)
    for name in TRACKED_FIELDS:
        if name not in by_field:
            continue
        c, w, m, n = tally(by_field[name])
        add(f"| {name} | {c} | {w} | {m} | {c / n:.0%} |" if n else
            f"| {name} | — | — | — | n/a |")
    add("")

    add("## By document condition")
    add("")
    add("| Condition | Docs | Accuracy | Wrong values | Mean time |")
    add("|---|---:|---:|---:|---:|")
    by_condition: dict[str, list[PolicyResult]] = defaultdict(list)
    for r in results:
        by_condition[r.condition].append(r)
    for condition, group in sorted(by_condition.items()):
        fields = [f for r in group for f in r.fields]
        c, w, m, n = tally(fields)
        add(f"| {condition} | {len(group)} | {c / n:.0%} | {w} | "
            f"{sum(r.seconds for r in group) / len(group):.1f}s |" if n else
            f"| {condition} | {len(group)} | n/a | 0 | — |")
    add("")

    all_fields = [f for r in results for f in r.fields]
    c, w, m, n = tally(all_fields)
    questions = sum(r.questions for r in results)
    add(f"**Overall: {c}/{n} correct ({c / n:.1%}), "
        f"{w} wrong values, {m} missing, {questions} questions raised.**")
    add("")

    wrong = [
        (r, f) for r in results for f in r.fields if f.outcome == Outcome.WRONG
    ]
    if wrong:
        add("## Wrong values")
        add("")
        add("These matter most: a confident incorrect figure is never questioned.")
        add("")
        add("| Policy | Condition | Field | Expected | Got | Confidence |")
        add("|---|---|---|---:|---:|---:|")
        for r, f in wrong[:20]:
            add(f"| {r.policy_id} | {r.condition} | {f.field} | {f.expected} | "
                f"{f.got} | {f.confidence:.2f} |")
        add("")

    errors = [r for r in results if r.error]
    if errors:
        add("## Errors")
        add("")
        for r in errors[:10]:
            add(f"- {r.policy_id} / {r.condition}: {r.error}")
        add("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark clause extraction.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--condition", action="append")
    parser.add_argument("--no-model", action="store_true",
                        help="rules only, to isolate the model's contribution")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip the challenge loop, to isolate its effect")
    args = parser.parse_args()

    started = time.perf_counter()
    results = run(
        limit=args.limit,
        conditions=set(args.condition) if args.condition else None,
        use_model=not args.no_model,
        verify_clauses=not args.no_verify,
    )
    text = report(results)
    print(text)
    print(f"\ncompleted in {time.perf_counter() - started:.0f}s")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = ("_rules_only" if args.no_model else "") + ("_unverified" if args.no_verify else "")
    out = REPORTS_DIR / f"extract_bench{suffix}.md"
    out.write_text(text, encoding="utf-8")
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
