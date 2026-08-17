"""Turn clean policy PDFs into the documents people actually upload.

Most users are not going to hand this system a pristine digital PDF. They will
photograph a policy on a kitchen table under a ceiling light, or send a PDF that
a shop assembled from photocopies and which contains no selectable text at all.
An OCR stage tuned only on clean renders will look excellent in testing and fall
apart on the first real upload.

Each profile below reproduces one real failure mode, and the whole set becomes
the benchmark the intake stage is scored against.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import cv2
import fitz
import numpy as np


@dataclass(frozen=True)
class DegradationProfile:
    """One way a document arrives damaged."""

    name: str
    dpi: int
    rotation_deg: float
    perspective: float
    """0 = flat-on; higher warps the page as if shot at an angle."""
    lighting: float
    """0 = even; higher adds a directional shadow and vignette."""
    blur: int
    """Gaussian kernel size; 0 disables."""
    noise: float
    jpeg_quality: int
    binarize: bool = False
    description: str = ""


PROFILES: list[DegradationProfile] = [
    DegradationProfile(
        name="clean_scan", dpi=300, rotation_deg=0.0, perspective=0.0,
        lighting=0.0, blur=0, noise=2.0, jpeg_quality=95,
        description="Flatbed scan, good conditions. The easy case.",
    ),
    DegradationProfile(
        name="skewed_scan", dpi=250, rotation_deg=2.4, perspective=0.0,
        lighting=0.12, blur=0, noise=5.0, jpeg_quality=85,
        description="Fed through the scanner crooked.",
    ),
    DegradationProfile(
        name="phone_photo", dpi=200, rotation_deg=-1.6, perspective=0.030,
        lighting=0.42, blur=3, noise=9.0, jpeg_quality=72,
        description="Handheld photo at an angle, indoor lighting.",
    ),
    DegradationProfile(
        name="dark_photo", dpi=180, rotation_deg=3.1, perspective=0.045,
        lighting=0.68, blur=3, noise=13.0, jpeg_quality=60,
        description="Underexposed photo with a strong shadow across the page.",
    ),
    DegradationProfile(
        name="photocopy", dpi=150, rotation_deg=-0.9, perspective=0.0,
        lighting=0.20, blur=0, noise=16.0, jpeg_quality=55, binarize=True,
        description="Several-generation photocopy, harsh contrast, speckled.",
    ),
]

PROFILES_BY_NAME = {p.name: p for p in PROFILES}


def rasterize(pdf_path: Path, dpi: int) -> list[np.ndarray]:
    """Render each page to a BGR image."""
    pages: list[np.ndarray] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            buf = np.frombuffer(pix.samples, dtype=np.uint8)
            img = buf.reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            pages.append(img)
    return pages


def _rotate(img: np.ndarray, degrees: float) -> np.ndarray:
    if not degrees:
        return img
    h, w = img.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), degrees, 1.0)
    return cv2.warpAffine(
        img, matrix, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _perspective(img: np.ndarray, strength: float, rng: random.Random) -> np.ndarray:
    """Warp as though photographed off-axis."""
    if strength <= 0:
        return img
    h, w = img.shape[:2]

    def jitter() -> float:
        return rng.uniform(-strength, strength)

    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([
        [w * jitter(), h * jitter()],
        [w * (1 + jitter()), h * jitter()],
        [w * (1 + jitter()), h * (1 + jitter())],
        [w * jitter(), h * (1 + jitter())],
    ])
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(
        img, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )


def _lighting(img: np.ndarray, strength: float, rng: random.Random) -> np.ndarray:
    """Directional shadow plus vignette — what a ceiling light does to paper."""
    if strength <= 0:
        return img
    h, w = img.shape[:2]

    # Linear gradient at a random angle.
    angle = rng.uniform(0, 2 * np.pi)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    gradient = (xs / w) * np.cos(angle) + (ys / h) * np.sin(angle)
    gradient = (gradient - gradient.min()) / (np.ptp(gradient) + 1e-6)

    # Vignette darkening toward the corners.
    cy, cx = h / 2, w / 2
    radial = np.sqrt(((ys - cy) / cy) ** 2 + ((xs - cx) / cx) ** 2)
    radial = np.clip(radial / np.sqrt(2), 0, 1)

    shade = 1.0 - strength * (0.62 * gradient + 0.38 * radial)
    shade = np.clip(shade, 0.25, 1.0)[:, :, None]
    return np.clip(img.astype(np.float32) * shade, 0, 255).astype(np.uint8)


def _noise(img: np.ndarray, sigma: float, rng: random.Random) -> np.ndarray:
    if sigma <= 0:
        return img
    generator = np.random.default_rng(rng.randint(0, 2**31 - 1))
    grain = generator.normal(0, sigma, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + grain, 0, 255).astype(np.uint8)


def _binarize(img: np.ndarray) -> np.ndarray:
    """Hard threshold, as a photocopier would, then re-expand to colour."""
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 12
    )
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def _jpeg(img: np.ndarray, quality: int) -> np.ndarray:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR) if ok else img


def degrade_page(
    img: np.ndarray, profile: DegradationProfile, rng: random.Random
) -> np.ndarray:
    """Apply a profile in the order the damage really happens.

    Geometry first (the page was crooked when it was captured), then optics,
    then sensor noise, then compression — which is the order that produces
    realistic artefacts rather than a stack of independent-looking filters.
    """
    out = _rotate(img, profile.rotation_deg + rng.uniform(-0.4, 0.4))
    out = _perspective(out, profile.perspective, rng)
    if profile.blur:
        k = profile.blur | 1  # kernel must be odd
        out = cv2.GaussianBlur(out, (k, k), 0)
    out = _lighting(out, profile.lighting, rng)
    out = _noise(out, profile.noise, rng)
    if profile.binarize:
        out = _binarize(out)
    return _jpeg(out, profile.jpeg_quality)


def write_image_pdf(pages: list[np.ndarray], path: Path, dpi: int) -> Path:
    """Assemble images into a PDF carrying no text layer.

    This is the case the problem statement calls out directly: a PDF that looks
    like a document but is really a stack of pictures, so text extraction
    returns nothing and OCR is the only way in.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for img in pages:
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        if not ok:
            continue
        h, w = img.shape[:2]
        # Convert pixel dimensions back to PDF points at the capture DPI.
        rect = fitz.Rect(0, 0, w * 72.0 / dpi, h * 72.0 / dpi)
        page = doc.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, stream=buf.tobytes())
    doc.save(path)
    doc.close()
    return path


def degrade_pdf(
    source: Path, profile: DegradationProfile, out_path: Path, seed: int = 0
) -> Path:
    """Produce a scanned-looking, text-free copy of a policy PDF."""
    rng = random.Random(seed)
    pages = [degrade_page(p, profile, rng) for p in rasterize(source, profile.dpi)]
    return write_image_pdf(pages, out_path, profile.dpi)


def degrade_to_photo(
    source: Path, profile: DegradationProfile, out_path: Path, seed: int = 0,
    page_index: int = 0,
) -> Path:
    """A single JPG, as if someone photographed one page and uploaded it."""
    rng = random.Random(seed)
    pages = rasterize(source, profile.dpi)
    img = degrade_page(pages[page_index], profile, rng)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), img, [int(cv2.IMWRITE_JPEG_QUALITY), profile.jpeg_quality])
    return out_path
