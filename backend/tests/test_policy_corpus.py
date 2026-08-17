"""M3, synthetic policy corpus.

The corpus is the measuring instrument for everything downstream, so it is
tested harder than the thing it measures. If ground truth is wrong, extraction
accuracy is meaningless and every later optimisation is guesswork.

Rendering is slow, so document-level tests render one or two policies rather
than the full set; the full build is exercised by `python -m datagen.build_all`.
"""

from __future__ import annotations

from decimal import Decimal

import fitz
import pytest

from app.schemas.policy import RoomLimitBasis
from datagen.degrade import PROFILES, degrade_page, degrade_to_photo, rasterize
from datagen.policies import (
    _in_words,
    blueprint_to_truth,
    make_blueprints,
    write_amount,
)
from datagen.render_pdf import render_policy_pdf


@pytest.fixture(scope="module")
def blueprints():
    return make_blueprints(40)


# --- amount rendering -----------------------------------------------------


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("rs_grouped", "Rs. 5,00,000/-"),
        ("inr_grouped", "INR 5,00,000"),
        ("symbol", "₹5,00,000"),
        ("lakh_decimal", "Rs. 5.00 Lakhs"),
        ("words", "Rupees Five Lakh Only"),
    ],
)
def test_amount_styles_render_as_indian_documents_write_them(style, expected):
    assert write_amount(500000, style) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (500000, "Five Lakh"),
        (1000000, "Ten Lakh"),
        (1500000, "Fifteen Lakh"),
        (2500000, "Twenty Five Lakh"),
        (10000000, "One Crore"),
        (325000, "Three Lakh Twenty Five Thousand"),
    ],
)
def test_indian_number_words(value, expected):
    assert _in_words(value) == expected


def test_amounts_survive_a_round_trip_through_the_money_parser():
    """Whatever style a document uses, the parser must recover the figure."""
    from app.schemas.money import to_decimal

    for style in ("rs_grouped", "inr_grouped", "symbol"):
        rendered = write_amount(750000, style)
        assert to_decimal(rendered) == Decimal(750000), (style, rendered)


# --- ground truth ---------------------------------------------------------


def test_every_blueprint_produces_usable_truth(blueprints):
    for bp in blueprints:
        truth = blueprint_to_truth(bp)
        assert truth.is_usable
        assert truth.sum_insured == Decimal(bp.sum_insured)
        assert truth.policy_id == bp.policy_id


def test_room_limit_truth_matches_each_phrasing(blueprints):
    for bp in blueprints:
        limit = blueprint_to_truth(bp).room_limit
        si = Decimal(bp.sum_insured)

        if bp.room_basis == "flat":
            assert limit.basis is RoomLimitBasis.FLAT_PER_DAY
            assert limit.effective_daily_cap(si) == Decimal(bp.room_flat)
        elif bp.room_basis == "pct":
            expected = si * Decimal(str(bp.room_pct)) / 100
            assert limit.effective_daily_cap(si) == expected
        elif bp.room_basis == "pct_with_max":
            # The lower of the percentage and the stated maximum must bind.
            pct_value = si * Decimal(str(bp.room_pct)) / 100
            assert limit.effective_daily_cap(si) == min(pct_value, Decimal(bp.room_flat))
        elif bp.room_basis == "category":
            assert limit.effective_daily_cap(si) is None
            assert limit.category_ceiling is not None
        else:
            assert limit.effective_daily_cap(si) is None


def test_corpus_covers_every_room_phrasing(blueprints):
    assert {bp.room_basis for bp in blueprints} == {
        "flat", "pct", "pct_with_max", "category", "none"
    }


def test_corpus_includes_contradiction_and_top_up_cases(blueprints):
    # Both exercise logic that a uniform corpus would never reach.
    assert sum(bp.contradicts_wording for bp in blueprints) >= 2
    assert sum(bp.is_top_up for bp in blueprints) >= 2
    for bp in blueprints:
        if bp.is_top_up:
            assert blueprint_to_truth(bp).deductible > 0


def test_sublimits_carry_through_to_truth(blueprints):
    bp = next(b for b in blueprints if b.sublimits)
    truth = blueprint_to_truth(bp)
    assert len(truth.sublimits) == len(bp.sublimits)


# --- rendered documents ---------------------------------------------------


@pytest.fixture(scope="module")
def rendered(tmp_path_factory, blueprints):
    path = tmp_path_factory.mktemp("pdf") / "policy.pdf"
    bp = next(b for b in blueprints if b.room_basis == "pct_with_max")
    render_policy_pdf(bp, path)
    return bp, path


def test_rendered_policy_has_schedule_and_wording(rendered):
    _, path = rendered
    with fitz.open(path) as doc:
        assert doc.page_count == 2
        schedule = doc[0].get_text()
        wording = doc[1].get_text()

    assert "POLICY SCHEDULE" in schedule
    assert "SCHEDULE OF BENEFITS" in schedule
    assert "POLICY WORDING" in wording
    assert "PERMANENT EXCLUSIONS" in wording


def test_the_actual_figures_appear_on_the_schedule_page(rendered):
    """Extraction can only find what was really printed."""
    bp, path = rendered
    with fitz.open(path) as doc:
        schedule = doc[0].get_text()

    assert bp.policy_number in schedule
    assert bp.policyholder in schedule
    assert "Room Rent Limit" in schedule
    assert f"{bp.room_pct:g}%" in schedule


def test_decoy_figures_sit_next_to_the_real_ones(rendered):
    """Premium and GST are the most attractive wrong answers in the document."""
    bp, path = rendered
    with fitz.open(path) as doc:
        schedule = doc[0].get_text()
    assert "Net Premium" in schedule
    assert "GST" in schedule
    assert bp.premium != bp.sum_insured


def test_text_layer_is_extractable(rendered):
    _, path = rendered
    with fitz.open(path) as doc:
        chars = sum(len(page.get_text().strip()) for page in doc)
    assert chars > 1500


# --- degradation ----------------------------------------------------------


def test_degraded_pdf_has_no_text_layer(rendered, tmp_path):
    """The case the problem statement calls out: a PDF built from images."""
    from datagen.degrade import degrade_pdf

    _, source = rendered
    out = degrade_pdf(source, PROFILES[2], tmp_path / "scanned.pdf", seed=1)
    with fitz.open(out) as doc:
        assert doc.page_count == 2
        assert sum(len(page.get_text().strip()) for page in doc) == 0


def test_every_profile_alters_the_page(rendered):
    import numpy as np

    _, source = rendered
    for profile in PROFILES:
        pages = rasterize(source, profile.dpi)
        import random

        degraded = degrade_page(pages[0], profile, random.Random(7))
        assert degraded.shape == pages[0].shape
        # Even the gentlest profile adds noise, so nothing should be identical.
        assert not np.array_equal(degraded, pages[0]), profile.name


def test_degradation_is_deterministic_for_a_seed(rendered, tmp_path):
    import numpy as np
    import cv2

    _, source = rendered
    a = degrade_to_photo(source, PROFILES[2], tmp_path / "a.jpg", seed=5)
    b = degrade_to_photo(source, PROFILES[2], tmp_path / "b.jpg", seed=5)
    assert np.array_equal(cv2.imread(str(a)), cv2.imread(str(b)))


def test_harsher_profiles_are_ordered_by_difficulty():
    names = [p.name for p in PROFILES]
    assert names.index("clean_scan") < names.index("phone_photo")
    assert PROFILES[0].dpi > PROFILES[-1].dpi
    assert PROFILES[0].noise < PROFILES[-1].noise


def test_photo_output_is_a_single_page(rendered, tmp_path):
    import cv2

    _, source = rendered
    out = degrade_to_photo(source, PROFILES[3], tmp_path / "photo.jpg", seed=2)
    img = cv2.imread(str(out))
    assert img is not None
    assert img.shape[0] > 500 and img.shape[1] > 400
