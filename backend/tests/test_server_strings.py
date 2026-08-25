"""Every sentence the server writes can be read in every language it speaks.

The interface's own words are checked on the frontend, by a script that reads
the JSX and the language tables together. These sentences are not in the JSX:
they are composed here, where the policy and the bill are, and they travel with
the key they are read under. Nothing on that side can see where those keys come
from, so nothing on that side can notice one going missing.

This is the other half of that check, run from the side the keys are born on.
It exercises the paths that produce them and asserts each key it sees has a
line in every language file. A sentence added here without one renders English
for a reader who chose Kannada, silently and forever, and that is exactly the
failure this project keeps saying it is against.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.journey import checklist, tracker
from app.pipeline.s6_simulate import eligibility, waterfall
from app.schemas.journey import JourneyStage, JourneyState
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    PolicyMeta,
    RoomCategory,
    RoomLimit,
    SubLimit,
    WaitingKind,
    WaitingPeriod,
)
from app.schemas.procedure import CostSplit, Procedure, Specialty
from app.schemas.simulation import BillLine, EstimatedBill

LANGS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "lang"
CODES = ("hi", "kn", "mr", "te")


def _table(code: str) -> set[str]:
    body = (LANGS / f"{code}.js").read_text()
    return set(re.findall(r"^\s*'([a-zA-Z][a-zA-Z0-9._]*)':", body, re.M))


@pytest.fixture(scope="module")
def tables() -> dict[str, set[str]]:
    return {code: _table(code) for code in CODES}


def _assert_reads(keys: set[str], prefix: str, tables: dict[str, set[str]]) -> None:
    missing = sorted(
        f"{code}: {prefix}{key}"
        for code in CODES
        for key in keys
        if f"{prefix}{key}" not in tables[code]
    )
    assert not missing, "no translation for:\n  " + "\n  ".join(missing)


def _policy(**over) -> NormalizedPolicy:
    fields = dict(
        sum_insured=Decimal(500000),
        meta=PolicyMeta(insurer_name="Test Insurer", start_date=date(2026, 1, 1)),
        room_limit=RoomLimit(basis="flat_per_day", amount_per_day=Decimal(5000)),
        copay_pct=Decimal(10),
        copay_above_age=61,
        deductible=Decimal(0),
        covers_consumables=False,
        pre_hospitalisation_days=30,
        post_hospitalisation_days=60,
        sublimits=[SubLimit(head=ExpenseHead.INVESTIGATIONS, amount=Decimal(5000))],
        restore_benefit=True,
    )
    return NormalizedPolicy(**(fields | over))


def _procedure(**over) -> Procedure:
    fields = dict(
        code="P1", name="Test treatment", specialty=Specialty.CARDIOLOGY,
        base_rate_non_nabh=Decimal(100000), base_rate_nabh=Decimal(120000),
        cost_split=CostSplit(fractions={ExpenseHead.SURGEON_FEE: 1.0}),
    )
    return Procedure(**(fields | over))


def _bill() -> EstimatedBill:
    return EstimatedBill(
        hospital_id="H1", procedure_code="P1",
        room_category=RoomCategory.SINGLE_PRIVATE,
        los_days=4, icu_days=1, room_rate_per_day=Decimal(9000),
        lines=[
            BillLine(head=ExpenseHead.ROOM_RENT, amount=Decimal(27000)),
            BillLine(head=ExpenseHead.ICU_CHARGES, amount=Decimal(12000)),
            BillLine(head=ExpenseHead.SURGEON_FEE, amount=Decimal(60000)),
            BillLine(head=ExpenseHead.INVESTIGATIONS, amount=Decimal(20000)),
            BillLine(head=ExpenseHead.CONSUMABLES, amount=Decimal(6000)),
            BillLine(head=ExpenseHead.NON_MEDICAL, amount=Decimal(2000)),
        ],
    )


def test_every_checklist_item_reads_in_every_language(tables):
    """All four stages, and the items that only appear on some policies."""
    keys: set[str] = set()
    for stage in (
        JourneyStage.PRE_ADMISSION, JourneyStage.ADMITTED,
        JourneyStage.DISCHARGE_PLANNING, JourneyStage.SETTLED,
    ):
        state = JourneyState(
            stage=stage,
            room_category=RoomCategory.SINGLE_PRIVATE,
            room_rate_per_day=Decimal(9000),
            admitted_at=datetime(2026, 8, 1, tzinfo=UTC),
        )
        procedure = _procedure(requires_implant=True)
        for item in checklist.items_for(state, _policy(), procedure=procedure):
            keys.add(item.string_key)
            keys.add(item.string_key + ".why")
    _assert_reads(keys, "checklist.", tables)


def test_every_deduction_reads_in_every_language(tables):
    """Both wordings of the two deductions that have two."""
    keys: set[str] = set()
    for policy in (_policy(), _policy(covers_consumables=True, copay_above_age=None)):
        result = waterfall.simulate(
            policy, _bill(), room_category=RoomCategory.SINGLE_PRIVATE,
            patient_age=70, is_network=False,
        )
        for step in result.steps:
            keys.add(step.kind.value)
            keys.add(step.string_key + ".why")
    _assert_reads(keys, "waterfall.", tables)


def test_every_warning_and_note_reads_in_every_language(tables):
    said: set[str] = set()
    for policy in (
        _policy(),
        _policy(covers_consumables=True, copay_above_age=None),
        _policy(sum_insured=Decimal(20000)),
        _policy(room_limit=RoomLimit(basis="category_only",
                                     category_ceiling=RoomCategory.TWIN_SHARING)),
    ):
        result = waterfall.simulate(
            policy, _bill(), room_category=RoomCategory.SINGLE_PRIVATE,
            patient_age=30, is_network=False,
        )
        said |= {p.key for p in [*result.warnings, *result.notes]}
    _assert_reads(said, "", tables)


def test_every_alert_reads_in_every_language(tables):
    state = JourneyState(
        stage=JourneyStage.ADMITTED,
        room_category=RoomCategory.SINGLE_PRIVATE,
        room_rate_per_day=Decimal(9000),
        admitted_at=datetime(2026, 8, 1, tzinfo=UTC),
    )
    policy = _policy()
    for head, amount in (
        (ExpenseHead.ROOM_RENT, "27000"), (ExpenseHead.SURGEON_FEE, "60000"),
        (ExpenseHead.INVESTIGATIONS, "6000"), (ExpenseHead.NON_MEDICAL, "3000"),
    ):
        tracker.record_cost(state, head, Decimal(amount), policy)

    keys: set[str] = set()
    for alert in tracker.evaluate(state, policy):
        keys.add(alert.string_key)
        keys.add(alert.string_key + ".msg")
        keys.add(alert.string_key + ".do")
    assert keys, "the scenario produced no alerts, so this proves nothing"
    _assert_reads(keys, "alert.", tables)


# The stay's timeline is recorded and carried in the journey payload, but no
# longer drawn: "what has happened so far" was a panel on the stay screen and
# said nothing the charges and the stage marker did not already say. There is
# accordingly nothing for a reader's own language to be checked against, and a
# test asserting otherwise would be asserting against tables that no call site
# reaches. If it is ever put back on screen, its keys come back with it.


def test_every_eligibility_finding_reads_in_every_language(tables):
    """Each waiting kind, at each of the three ways a wait is described."""
    procedure = _procedure(is_daycare=True)
    keys: set[str] = set()
    for months, days in ((0, 30), (24, 0), (48, 0)):
        for kind, applies in (
            (WaitingKind.INITIAL, "any"),
            (WaitingKind.PRE_EXISTING, "pre-existing diseases"),
            (WaitingKind.SPECIFIC_AILMENT, "test"),
        ):
            policy = _policy(
                covers_daycare=False,
                waiting_periods=[WaitingPeriod(
                    months=months, days=days, kind=kind, applies_to=applies,
                )],
            )
            for pre_existing in (None, True):
                found = eligibility.assess(
                    policy, procedure, on=date(2026, 2, 1),
                    pre_existing=pre_existing,
                )
                for finding in found.findings:
                    keys.add(finding.key)
                    keys.add(finding.key + ".detail")
    keys.discard("")
    keys.discard(".detail")
    _assert_reads(keys, "elig.", tables)


# The bill reader's findings are not checked here any more.
#
# Reading a hospital bill and saying what is worth raising about it is still
# what `app.bill` does, still exercised by tests/test_bill_*.py and still
# scored by bench/. What it no longer has is a screen: the stay page files the
# paper behind each charge as that charge is entered, and the panel that took a
# whole final bill and reported on it is gone. Nothing renders these sentences,
# so there is no reader to have them in their own language, and a test
# asserting four translations of them would be asserting against tables no call
# site reaches. Give it a screen again and its keys come back with it.


def test_the_language_files_agree_with_each_other(tables):
    """A key in one and not another is the same silence, one language along."""
    reference = tables["hi"]
    for code in CODES[1:]:
        assert tables[code] == reference, f"{code} and hi hold different keys"
