"""M2, dataset generation.

The corpus is synthetic, so the thing worth testing is not the values but the
*structure*: that attributes correlate the way real ones do, that the build is
reproducible, and that nothing downstream can be handed an incoherent record.

The correlation tests matter most. If price, quality and network status were
independent random draws, every hospital would be interchangeable and the
ranking engine would have no real trade-offs to reason about, the demo would
look fine and mean nothing.
"""

from __future__ import annotations

import pytest

from app.schemas.hospital import Accreditation, HospitalType
from app.schemas.policy import RoomCategory
from datagen.build_all import validate
from datagen.hospitals import build_hospitals
from datagen.insurers import build_insurers
from datagen.procedures import ARCHETYPES, build_procedures


@pytest.fixture(scope="module")
def corpus():
    procedures = build_procedures()
    hospitals = build_hospitals(procedures)
    insurers = build_insurers()
    return procedures, hospitals, insurers


# --- integrity ------------------------------------------------------------


def test_corpus_passes_its_own_validation(corpus):
    assert validate(*corpus) == []


def test_generation_is_reproducible():
    # A corpus that shifts between machines makes every golden test unstable.
    procedures = build_procedures()
    first = build_hospitals(procedures)
    second = build_hospitals(procedures)
    assert [h.hospital_id for h in first] == [h.hospital_id for h in second]
    assert [h.name for h in first] == [h.name for h in second]
    assert first[17].room_tariffs == second[17].room_tariffs


def test_every_archetype_sums_to_one():
    for name, fractions in ARCHETYPES.items():
        assert sum(fractions.values()) == pytest.approx(1.0, abs=0.005), name


def test_cost_splits_reconcile_for_every_procedure(corpus):
    procedures, _, _ = corpus
    for proc in procedures:
        parts = proc.cost_split.apply(proc.base_rate_non_nabh)
        assert sum(parts.values()) == proc.base_rate_non_nabh, proc.code


# --- correlation structure ------------------------------------------------


def test_accredited_hospitals_charge_more(corpus):
    _, hospitals, _ = corpus
    private = [h for h in hospitals if h.hospital_type is HospitalType.PRIVATE]

    def median_rate(accreditations: set[Accreditation]) -> float:
        rates = sorted(
            float(t.per_day)
            for h in private
            if h.quality.accreditation in accreditations
            and (t := h.tariff_for(RoomCategory.SINGLE_PRIVATE))
        )
        return rates[len(rates) // 2]

    assert median_rate({Accreditation.NABH_FULL, Accreditation.JCI}) > median_rate(
        {Accreditation.NONE}
    )


def test_government_hospitals_are_far_cheaper(corpus):
    """The affordability escape hatch the relaxation ladder depends on."""
    _, hospitals, _ = corpus

    def median_ward(hospital_type: HospitalType) -> float:
        rates = sorted(
            float(t.per_day)
            for h in hospitals
            if h.hospital_type is hospital_type
            and (t := h.tariff_for(RoomCategory.GENERAL_WARD))
        )
        return rates[len(rates) // 2]

    assert median_ward(HospitalType.GOVERNMENT) < median_ward(HospitalType.PRIVATE) / 3


def test_larger_hospitals_reach_more_networks(corpus):
    _, hospitals, _ = corpus
    private = [h for h in hospitals if h.hospital_type is HospitalType.PRIVATE]
    small = [h for h in private if h.quality.bed_count < 80]
    large = [h for h in private if h.quality.bed_count > 280]

    def mean_networks(subset):
        return sum(len(h.cashless_insurers) for h in subset) / len(subset)

    assert mean_networks(large) > mean_networks(small) * 1.5


def test_room_rates_rise_monotonically_with_tier(corpus):
    _, hospitals, _ = corpus
    for hospital in hospitals:
        ladder = sorted(
            (t for t in hospital.room_tariffs if t.category is not RoomCategory.ICU),
            key=lambda t: t.category.rank,
        )
        rates = [t.per_day for t in ladder]
        assert rates == sorted(rates), hospital.hospital_id


def test_bigger_hospitals_offer_more_specialties(corpus):
    _, hospitals, _ = corpus
    small = [h for h in hospitals if h.quality.bed_count < 80]
    large = [h for h in hospitals if h.quality.bed_count > 280]
    assert (
        sum(h.quality.specialty_count for h in large) / len(large)
        > sum(h.quality.specialty_count for h in small) / len(small)
    )


# --- realism the pipeline depends on --------------------------------------


def test_some_hospitals_sit_outside_every_network(corpus):
    """Otherwise the non-network relaxation tier could never be exercised."""
    _, hospitals, _ = corpus
    orphans = [h for h in hospitals if not h.cashless_insurers]
    assert len(orphans) / len(hospitals) > 0.10


def test_beds_are_genuinely_scarce(corpus):
    """Availability must be a real constraint, not a rubber stamp."""
    _, hospitals, _ = corpus
    full = [h for h in hospitals if not h.available_rooms()]
    assert len(full) > 0
    assert len(full) / len(hospitals) < 0.5


def test_private_rooms_commonly_exceed_a_typical_room_cap(corpus):
    """A 5 lakh policy capping room rent at 1% allows Rs. 5,000 per day.

    If most private rooms sat under that, proportionate deduction would be a
    feature nobody ever sees. They do not, and that is the point.
    """
    _, hospitals, _ = corpus
    rates = [
        t.per_day
        for h in hospitals
        if h.hospital_type is HospitalType.PRIVATE
        and (t := h.tariff_for(RoomCategory.SINGLE_PRIVATE))
    ]
    over_cap = sum(1 for r in rates if r > 5000)
    assert over_cap / len(rates) > 0.5


def test_procedures_span_a_wide_cost_range(corpus):
    procedures, _, _ = corpus
    rates = sorted(p.base_rate_non_nabh for p in procedures)
    assert rates[0] < 15000
    assert rates[-1] > 300000


def test_every_city_has_hospitals_for_common_specialties(corpus):
    _, hospitals, _ = corpus
    cities = {h.city for h in hospitals}
    assert len(cities) == 4
    for city in cities:
        in_city = [h for h in hospitals if h.city == city]
        assert any("cardiology" in h.specialties for h in in_city), city
        assert any("general_surgery" in h.specialties for h in in_city), city


def test_nabh_rate_premium_is_applied(corpus):
    procedures, _, _ = corpus
    for proc in procedures:
        ratio = proc.base_rate_nabh / proc.base_rate_non_nabh
        assert 1.10 < float(ratio) < 1.20, proc.code
