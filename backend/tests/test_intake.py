"""M4, document intake and the OCR ladder.

Detector tests use synthetic images with known defects rather than corpus
documents, so a failure points at one specific piece of logic instead of at
"OCR got worse". The detectors matter more than they look: preprocessing is
adaptive, so misclassifying a page means applying the wrong filter, and the
wrong filter costs more accuracy than doing nothing at all.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from app.pipeline.s0_intake import ocr, preprocess
from app.schemas.document import IngestedDocument, InputKind, Page, SourceMode, Word
from app.schemas.policy import BoundingBox

# --- helpers --------------------------------------------------------------


def make_page(text_lines: int = 14, width: int = 1240, height: int = 1754) -> np.ndarray:
    """A synthetic document page: dark text rows on white paper."""
    img = np.full((height, width, 3), 255, np.uint8)
    for i in range(text_lines):
        y = 120 + i * 90
        cv2.putText(
            img, f"Sum Insured Rs. {i + 1},00,000 per policy year",
            (90, y), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (10, 10, 10), 2, cv2.LINE_AA,
        )
    return img


def add_speckle(img: np.ndarray, density: float = 0.02) -> np.ndarray:
    out = img.copy()
    rng = np.random.default_rng(3)
    mask = rng.random(img.shape[:2]) < density
    out[mask] = 0
    return out


def add_gradient(img: np.ndarray, strength: float = 0.7) -> np.ndarray:
    h, w = img.shape[:2]
    ramp = np.linspace(1.0, 1.0 - strength, w, dtype=np.float32)
    return np.clip(img.astype(np.float32) * ramp[None, :, None], 0, 255).astype(np.uint8)


def rotate(img: np.ndarray, degrees: float) -> np.ndarray:
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), degrees, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REPLICATE)


# --- skew estimation ------------------------------------------------------


@pytest.mark.parametrize("angle", [-3.0, -1.5, 1.0, 2.5])
def test_skew_estimate_recovers_an_injected_rotation(angle):
    # The estimator returns the correction, so it should be the negation.
    skewed = rotate(make_page(), angle)
    assert preprocess.estimate_skew(skewed) == pytest.approx(-angle, abs=0.6)


def test_straight_page_is_left_alone():
    _, applied = preprocess.deskew(make_page())
    assert applied == 0.0


def test_deskew_returns_the_angle_it_applied():
    rotated, applied = preprocess.deskew(rotate(make_page(), 2.0))
    assert applied != 0.0
    assert rotated.shape == make_page().shape


# --- page condition detectors --------------------------------------------


def test_speckle_detector_separates_photocopy_from_clean_scan():
    """The distinction the whole adaptive chain hangs on.

    A clean scan is strongly bimodal too, so a bimodality test classifies the
    easiest pages as the hardest. Counting undersized ink components does not.
    """
    clean = make_page()
    speckled = add_speckle(clean)

    assert not preprocess.is_speckled(clean)
    assert preprocess.is_speckled(speckled)
    assert preprocess.speckle_ratio(speckled) > preprocess.speckle_ratio(clean)


def test_lighting_detector_finds_a_gradient():
    clean = make_page()
    shadowed = add_gradient(clean)
    assert preprocess.lighting_unevenness(shadowed) > preprocess.lighting_unevenness(clean)
    assert preprocess.lighting_unevenness(shadowed) > preprocess.LIGHTING_UNEVENNESS_THRESHOLD


@pytest.mark.parametrize(
    ("height", "expected"),
    [(3508, 300), (1754, 150), (2339, 200)],
)
def test_dpi_is_inferred_from_page_size(height, expected):
    # Guessing too low upscales a good capture past Tesseract's useful range.
    img = np.full((height, int(height * 0.707), 3), 255, np.uint8)
    assert preprocess.estimate_dpi(img) == pytest.approx(expected, abs=3)


def test_dpi_estimate_is_bounded():
    assert preprocess.estimate_dpi(np.zeros((60, 40, 3), np.uint8)) >= 72
    assert preprocess.estimate_dpi(np.zeros((20000, 14000, 3), np.uint8)) <= 600


# --- filters --------------------------------------------------------------


def test_despeckle_removes_noise_and_keeps_text():
    clean = make_page()
    speckled = add_speckle(clean)
    cleaned = preprocess.despeckle(speckled)

    # Far less stray ink than the speckled input...
    assert preprocess.speckle_ratio(cleaned) < preprocess.speckle_ratio(speckled)

    # ...while the text itself survives. Character count alone cannot say that:
    # speckle invents characters as often as it hides them, so the noisy page
    # can out-count the cleaned one by a mark or two, and which way it falls
    # depends on the Tesseract build. What must hold is that the words are
    # still there and the engine is markedly surer of them.
    noisy, denoised = ocr.run(speckled), ocr.run(cleaned)
    assert denoised.char_count >= 0.9 * noisy.char_count
    assert denoised.mean_confidence > noisy.mean_confidence


def test_lighting_flattening_evens_out_a_shadow():
    shadowed = add_gradient(make_page())
    flattened = preprocess.flatten_lighting(shadowed)
    assert preprocess.lighting_unevenness(flattened) < preprocess.lighting_unevenness(shadowed)


def test_upscale_only_applies_below_the_target_dpi():
    img = make_page()
    unchanged, factor = preprocess.upscale_for_ocr(img, 300)
    assert factor == 1.0 and unchanged.shape == img.shape

    bigger, factor = preprocess.upscale_for_ocr(img, 150)
    assert factor == pytest.approx(2.0)
    assert bigger.shape[0] > img.shape[0]


def test_upscale_is_capped():
    _, factor = preprocess.upscale_for_ocr(make_page(), 20)
    assert factor <= preprocess.MAX_UPSCALE


# --- adaptive chain -------------------------------------------------------


def test_clean_page_skips_the_heavy_filters():
    """Preprocessing must never punish the common case."""
    result = preprocess.prepare(make_page(), source_dpi=300)
    assert not any("despeckle" in s for s in result.steps)
    assert "lighting" not in result.steps


def test_speckled_page_is_despeckled_and_not_run_through_non_local_means():
    result = preprocess.prepare(add_speckle(make_page()), source_dpi=300)
    assert any("despeckle" in s for s in result.steps)
    assert "denoise" not in result.steps


def test_shadowed_page_gets_its_lighting_flattened():
    result = preprocess.prepare(add_gradient(make_page()), source_dpi=300)
    assert "lighting" in result.steps


def test_preprocessing_improves_a_damaged_page():
    damaged = add_speckle(rotate(add_gradient(make_page()), 2.2), density=0.03)
    before = ocr.run(damaged)
    prepared = preprocess.prepare(damaged, source_dpi=300)
    after = ocr.run(prepared.image, scale_back=prepared.upscaled)
    assert after.char_count > before.char_count


def test_non_aggressive_mode_only_deskews():
    result = preprocess.prepare(add_speckle(make_page()), source_dpi=300, aggressive=False)
    assert not any("despeckle" in s for s in result.steps)
    assert "denoise" not in result.steps


# --- ocr ------------------------------------------------------------------


def test_tesseract_is_installed():
    assert ocr.is_available(), "install tesseract: brew install tesseract"


def test_ocr_returns_words_with_geometry_and_confidence():
    result = ocr.run(make_page())
    assert result.char_count > 50
    assert result.words
    assert all(0.0 <= w.confidence <= 1.0 for w in result.words)
    assert all(w.bbox.x1 > w.bbox.x0 for w in result.words)


def test_boxes_are_mapped_back_through_upscaling():
    """Boxes must refer to the original page, or evidence crops point nowhere."""
    img = make_page()
    upscaled, factor = preprocess.upscale_for_ocr(img, 150)
    assert factor > 1.0

    scaled = ocr.run(upscaled, scale_back=factor)
    assert scaled.words
    # Every box must sit inside the original page bounds, not the enlarged one.
    assert max(w.bbox.x1 for w in scaled.words) <= img.shape[1] + 2
    assert max(w.bbox.y1 for w in scaled.words) <= img.shape[0] + 2


def test_span_confidence_reflects_the_quoted_words_only():
    words = [
        Word(text="Sum", bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10), confidence=0.9),
        Word(text="Insured", bbox=BoundingBox(x0=11, y0=0, x1=20, y1=10), confidence=0.7),
        Word(text="rubbish", bbox=BoundingBox(x0=21, y0=0, x1=30, y1=10), confidence=0.1),
    ]
    assert ocr.confidence_of_span(words, "Sum Insured") == pytest.approx(0.8)
    assert ocr.confidence_of_span(words, "not present") is None


# --- document model -------------------------------------------------------


def test_quality_is_weighted_by_page_length():
    """A short perfect page must not mask a long bad one."""
    doc = IngestedDocument(
        filename="x.pdf", input_kind=InputKind.PDF_SCANNED,
        pages=[
            Page(page_index=0, width=600, height=800, text="ok " * 5,
                 source_mode=SourceMode.OCR,
                 words=[Word(text="ok", bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                             confidence=1.0)]),
            Page(page_index=1, width=600, height=800, text="bad " * 400,
                 source_mode=SourceMode.OCR,
                 words=[Word(text="bad", bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                             confidence=0.4)]),
        ],
    )
    assert doc.quality_score < 0.55


def test_native_pages_report_full_confidence():
    page = Page(page_index=0, width=600, height=800, text="exact text",
                source_mode=SourceMode.NATIVE)
    assert page.mean_confidence == 1.0


def test_bbox_lookup_finds_a_multi_word_span():
    page = Page(
        page_index=0, width=600, height=800, text="Sum Insured Rs. 5,00,000",
        source_mode=SourceMode.OCR,
        words=[
            Word(text="Sum", bbox=BoundingBox(x0=0, y0=0, x1=30, y1=12)),
            Word(text="Insured", bbox=BoundingBox(x0=32, y0=0, x1=90, y1=12)),
            Word(text="Rs.", bbox=BoundingBox(x0=92, y0=0, x1=110, y1=12)),
        ],
    )
    box = page.bbox_for_span("Sum Insured")
    assert box is not None
    assert box.x0 == 0 and box.x1 == 90
    assert page.bbox_for_span("Not There") is None


def test_crop_is_clamped_to_the_page():
    page = Page(page_index=0, width=100, height=100, source_mode=SourceMode.OCR)
    crop = page.crop_for(BoundingBox(x0=2, y0=2, x1=98, y1=98), pad=20)
    assert crop.x0 == 0 and crop.y0 == 0
    assert crop.x1 == 100 and crop.y1 == 100


def test_unreadable_upload_is_flagged_rather_than_answered():
    from app.pipeline.s0_intake.intake import _warn_if_poor

    doc = IngestedDocument(
        filename="blurry.jpg", input_kind=InputKind.IMAGE,
        pages=[Page(page_index=0, width=600, height=800, text="",
                    source_mode=SourceMode.EMPTY)],
    )
    _warn_if_poor(doc)
    assert doc.warnings
    assert "could not read" in doc.warnings[0].text.lower()


# --- end to end -----------------------------------------------------------


@pytest.fixture(scope="module")
def sample_policy(tmp_path_factory):
    from datagen.policies import make_blueprints
    from datagen.render_pdf import render_policy_pdf

    path = tmp_path_factory.mktemp("intake") / "policy.pdf"
    bp = make_blueprints(3)[0]
    render_policy_pdf(bp, path)
    return bp, path


def test_native_pdf_needs_no_ocr(sample_policy):
    from app.pipeline.s0_intake.intake import ingest

    _, path = sample_policy
    doc = ingest(path, session_id="test", save_page_images=False)

    assert doc.input_kind is InputKind.PDF_TEXT
    assert not doc.needed_ocr
    assert doc.quality_score == 1.0
    assert doc.total_chars > 1500
    assert not doc.warnings


def test_scanned_pdf_falls_through_to_ocr(sample_policy, tmp_path):
    from app.pipeline.s0_intake.intake import ingest
    from datagen.degrade import PROFILES_BY_NAME, degrade_pdf

    bp, path = sample_policy
    scanned = degrade_pdf(
        path, PROFILES_BY_NAME["clean_scan"], tmp_path / "scanned.pdf", seed=1
    )
    doc = ingest(scanned, session_id="test", save_page_images=False)

    assert doc.input_kind is InputKind.PDF_SCANNED
    assert doc.needed_ocr
    assert doc.is_usable
    # The figures that matter must survive, not just some text.
    assert bp.policy_number.replace(" ", "") in doc.full_text().replace(" ", "")
