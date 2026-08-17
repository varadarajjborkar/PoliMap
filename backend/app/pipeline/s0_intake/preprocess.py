"""Image preparation before OCR.

OCR accuracy on a photographed page is dominated by geometry, not by the
recogniser. A page tilted three degrees costs more accuracy than a fair amount
of noise does, because character segmentation assumes text sits on horizontal
baselines. So the work here is mostly about putting the page straight and
flattening the lighting, in that order.

Every operation is conservative: it either improves the image or leaves it
alone. A preprocessing step that damages an already-clean scan is worse than no
preprocessing, and clean scans are the common case.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

MIN_OCR_DPI = 300
MAX_UPSCALE = 2.5
DESKEW_SEARCH_DEG = 6.0
DESKEW_MIN_CORRECTION = 0.25
"""Below this the rotation is not worth the resampling blur."""


@dataclass
class PreprocessResult:
    image: np.ndarray
    rotation_applied_deg: float = 0.0
    perspective_corrected: bool = False
    upscaled: float = 1.0
    steps: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.steps is None:
            self.steps = []


def to_grey(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def estimate_skew(img: np.ndarray, search_deg: float = DESKEW_SEARCH_DEG) -> float:
    """Estimate page skew in degrees, positive meaning counter-clockwise.

    Uses a projection profile: rotating text to true horizontal maximises the
    variance of the row-sum profile, because rows then fall cleanly into dark
    text lines and bright gaps. This is slower than fitting a box around the
    text mask but far steadier on sparse pages and on tables, where a bounding
    box is dominated by rules rather than by the text baselines.
    """
    grey = to_grey(img)

    # Work at a reduced size; skew is a global property and full resolution
    # buys nothing but time.
    scale = min(1.0, 900 / max(grey.shape))
    if scale < 1.0:
        grey = cv2.resize(grey, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    binary = cv2.adaptiveThreshold(
        cv2.GaussianBlur(grey, (3, 3), 0), 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15,
    )

    if binary.sum() == 0:
        return 0.0

    def profile_variance(angle: float) -> float:
        h, w = binary.shape
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        rotated = cv2.warpAffine(
            binary, matrix, (w, h), flags=cv2.INTER_NEAREST, borderValue=0
        )
        return float(np.var(rotated.sum(axis=1, dtype=np.float64)))

    # Coarse sweep, then refine around the winner.
    coarse = np.arange(-search_deg, search_deg + 0.001, 0.5)
    best = max(coarse, key=profile_variance)
    fine = np.arange(best - 0.5, best + 0.5001, 0.1)
    return round(float(max(fine, key=profile_variance)), 2)


def deskew(img: np.ndarray) -> tuple[np.ndarray, float]:
    """Rotate the page upright. Returns the image and the angle applied."""
    angle = estimate_skew(img)
    if abs(angle) < DESKEW_MIN_CORRECTION:
        return img, 0.0

    h, w = img.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(
        img, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated, angle


def find_document_quad(img: np.ndarray) -> np.ndarray | None:
    """Locate the page outline in a photo that includes background.

    Returns None when no convincing quadrilateral is found, or when the one
    found covers nearly the whole frame: that means the page was scanned or
    cropped to its edges and there is no perspective to undo.
    """
    grey = to_grey(img)
    h, w = grey.shape
    frame_area = h * w

    edges = cv2.Canny(cv2.GaussianBlur(grey, (5, 5), 0), 40, 130)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        area = cv2.contourArea(contour)
        if area < frame_area * 0.30:
            break
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            if area > frame_area * 0.92:
                return None  # Page already fills the frame.
            return approx.reshape(4, 2).astype(np.float32)
    return None


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Order corners as top-left, top-right, bottom-right, bottom-left."""
    ordered = np.zeros((4, 2), dtype=np.float32)
    total = pts.sum(axis=1)
    ordered[0] = pts[np.argmin(total)]
    ordered[2] = pts[np.argmax(total)]
    diff = np.diff(pts, axis=1).ravel()
    ordered[1] = pts[np.argmin(diff)]
    ordered[3] = pts[np.argmax(diff)]
    return ordered


def correct_perspective(img: np.ndarray) -> tuple[np.ndarray, bool]:
    """Flatten an off-axis photo onto a rectangle."""
    quad = find_document_quad(img)
    if quad is None:
        return img, False

    corners = _order_corners(quad)
    tl, tr, br, bl = corners
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if width < 200 or height < 200:
        return img, False

    target = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    matrix = cv2.getPerspectiveTransform(corners, target)
    return cv2.warpPerspective(img, matrix, (width, height), flags=cv2.INTER_CUBIC), True


def flatten_lighting(img: np.ndarray) -> np.ndarray:
    """Remove a lighting gradient while keeping the text.

    Divides the page by a heavily blurred copy of itself, which approximates the
    illumination field. A shadow across one corner otherwise pushes that region
    below any global threshold and the text there is simply lost.
    """
    grey = to_grey(img)
    background = cv2.GaussianBlur(grey, (0, 0), sigmaX=max(grey.shape) / 28)
    background = np.where(background < 1, 1, background).astype(np.float32)
    normalised = (grey.astype(np.float32) / background) * 190.0
    return np.clip(normalised, 0, 255).astype(np.uint8)


SPECKLE_MIN_AREA = 6
"""Connected components smaller than this are specks, not characters."""


SPECKLE_RATIO_THRESHOLD = 0.35
LIGHTING_UNEVENNESS_THRESHOLD = 12.0


def speckle_ratio(img: np.ndarray) -> float:
    """Share of ink components too small to be characters.

    Bimodality is not the signal it looks like: a clean scan of black text on
    white paper is strongly bimodal too, so thresholding on it classifies the
    easiest pages as the hardest. What actually separates a photocopy from a
    clean scan is impulse noise: thousands of isolated specks, each far smaller
    than any glyph. Counting them survives the JPEG smearing that flattens the
    histogram and defeats a bimodality test.
    """
    grey = to_grey(img)
    scale = min(1.0, 1400 / max(grey.shape))
    if scale < 1.0:
        grey = cv2.resize(grey, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    ink = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if count <= 1:
        return 0.0

    areas = stats[1:, cv2.CC_STAT_AREA]
    return float((areas < SPECKLE_MIN_AREA).sum() / len(areas))


def is_speckled(img: np.ndarray) -> bool:
    return speckle_ratio(img) > SPECKLE_RATIO_THRESHOLD


def lighting_unevenness(img: np.ndarray) -> float:
    """Spread of paper brightness across the page.

    The text has to be removed before measuring, otherwise this reports how
    densely the page is written rather than how it was lit: a sparse page with
    a heading and wide margins varies just as much as a genuinely shadowed one,
    and flattening it would be wasted work on the commonest kind of document.

    Dilation takes the local maximum, which for dark text on light paper erases
    the glyphs and leaves the illumination field behind.
    """
    grey = to_grey(img)
    scale = min(1.0, 800 / max(grey.shape))
    if scale < 1.0:
        grey = cv2.resize(grey, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    paper = cv2.dilate(grey, np.ones((15, 15), np.uint8), iterations=2)
    small = cv2.resize(paper, (16, 16), interpolation=cv2.INTER_AREA)
    return float(np.std(small.astype(np.float32)))


HEAVY_SPECKLE_RATIO = 0.70


def despeckle(img: np.ndarray, ratio: float | None = None) -> np.ndarray:
    """Remove isolated specks from a noisy page.

    A median filter is the correct tool for impulse noise: it discards outlier
    pixels outright while leaving edges sharp. Non-local means, tuned for
    Gaussian noise, averages speckle into grey haze instead and leaves the page
    harder to read than it started. Anything the median misses is cleared by
    dropping connected components too small to be a character.

    The kernel scales with how badly the page is speckled. A wider window
    removes more noise but starts eating thin strokes, so it is reserved for
    pages where nearly every ink component is a speck and there is little left
    to protect.
    """
    grey = to_grey(img)
    if ratio is None:
        ratio = speckle_ratio(grey)
    kernel = 5 if ratio > HEAVY_SPECKLE_RATIO else 3
    filtered = cv2.medianBlur(grey, kernel)

    # Components are found on the ink; small ones are noise.
    ink = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if count <= 1:
        return filtered

    speck_mask = np.zeros(filtered.shape, dtype=bool)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] < SPECKLE_MIN_AREA:
            speck_mask |= labels == label

    cleaned = filtered.copy()
    cleaned[speck_mask] = 255
    return cleaned


def denoise(img: np.ndarray) -> np.ndarray:
    """Suppress noise using whichever method suits the page.

    Chosen by noise character rather than applied uniformly: the wrong denoiser
    costs far more accuracy than none at all.
    """
    if is_speckled(img):
        return despeckle(img)
    return cv2.fastNlMeansDenoising(
        to_grey(img), None, h=7, templateWindowSize=7, searchWindowSize=21
    )


A4_HEIGHT_INCHES = 11.69
A4_WIDTH_INCHES = 8.27
DPI_BOUNDS = (72, 600)


def estimate_dpi(img: np.ndarray) -> int:
    """Infer capture resolution from the image's pixel dimensions.

    An uploaded photo carries no reliable DPI metadata, but policy documents are
    A4, so the long edge in pixels divided by the page's long edge in inches is
    a good estimate. Guessing too low is actively harmful: the page then gets
    upscaled past the resolution Tesseract is tuned for, and accuracy falls even
    though the source was fine.
    """
    height, width = img.shape[:2]
    if height >= width:
        dpi = height / A4_HEIGHT_INCHES
    else:
        dpi = width / A4_HEIGHT_INCHES  # Landscape capture of a portrait page.
    return int(min(max(dpi, DPI_BOUNDS[0]), DPI_BOUNDS[1]))


def upscale_for_ocr(img: np.ndarray, source_dpi: int) -> tuple[np.ndarray, float]:
    """Enlarge low-resolution pages toward the DPI Tesseract expects."""
    if source_dpi >= MIN_OCR_DPI:
        return img, 1.0
    factor = min(MIN_OCR_DPI / source_dpi, MAX_UPSCALE)
    return (
        cv2.resize(img, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC),
        round(factor, 3),
    )


def prepare(
    img: np.ndarray,
    *,
    source_dpi: int = 300,
    aggressive: bool = True,
) -> PreprocessResult:
    """Full preparation chain, ordered so each step helps the next.

    Perspective comes first because every later measurement assumes a flat page.
    The middle of the chain then branches on what kind of page this is:

    * an already-thresholded page (photocopy, fax) is despeckled *before* skew
      is measured, because impulse noise swamps the projection profile and the
      estimator locks onto the speckle instead of the text baselines;
    * a greyscale page has its lighting flattened first so that thresholding and
      skew estimation both see even contrast, and is denoised after deskewing.

    Upscaling is last, so the expensive filters run on the smaller image.
    """
    result = PreprocessResult(image=img)

    flat, corrected = correct_perspective(img)
    if corrected:
        result.perspective_corrected = True
        result.steps.append("perspective")
    working = flat

    ratio = speckle_ratio(working) if aggressive else 0.0
    speckled = ratio > SPECKLE_RATIO_THRESHOLD
    uneven = aggressive and lighting_unevenness(working) > LIGHTING_UNEVENNESS_THRESHOLD

    if speckled:
        working = despeckle(working, ratio)
        result.steps.append(f"despeckle ({ratio:.0%} specks)")
    if uneven:
        working = flatten_lighting(working)
        result.steps.append("lighting")

    working, angle = deskew(working)
    if angle:
        result.rotation_applied_deg = angle
        result.steps.append(f"deskew {angle:+.2f}deg")

    if aggressive and not speckled:
        # Non-local means assumes Gaussian noise; on a despeckled page it would
        # only soften strokes the median filter already cleaned up.
        working = denoise(working)
        result.steps.append("denoise")

    working, factor = upscale_for_ocr(working, source_dpi)
    if factor > 1.0:
        result.upscaled = factor
        result.steps.append(f"upscale x{factor}")

    result.image = working
    return result
