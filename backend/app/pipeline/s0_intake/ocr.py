"""Tesseract wrapper producing word-level text with confidence and geometry.

Confidence is the point of this module. A flat transcription would be enough to
extract from, but not enough to know *when not to trust the extraction*. Because
per-word confidence is retained, the pipeline can escalate exactly the pages
that need a vision model, attach a recognition confidence to each clause, and
tell the user which figures deserve a second look — rather than treating a
guess on a shadowed page identically to a clean read.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field

import cv2
import numpy as np

from app.core.logging import get_logger
from app.schemas.document import Word
from app.schemas.policy import BoundingBox

log = get_logger(__name__)

# Page segmentation mode 3: fully automatic, no orientation assumption. Policy
# documents mix dense tables with prose, and the block-oriented modes split
# table cells badly.
DEFAULT_CONFIG = "--oem 3 --psm 3"
MIN_WORD_CONFIDENCE = 0.30
"""Below this a token is more likely noise than a word."""


@dataclass
class OcrResult:
    text: str = ""
    words: list[Word] = field(default_factory=list)
    mean_confidence: float = 0.0
    engine: str = "tesseract"

    @property
    def char_count(self) -> int:
        return len(self.text.strip())


def is_available() -> bool:
    return shutil.which("tesseract") is not None


def version() -> str:
    try:
        import pytesseract

        return str(pytesseract.get_tesseract_version())
    except Exception:
        return "unavailable"


def _scale_box(box: BoundingBox, factor: float) -> BoundingBox:
    """Map a box measured on an upscaled image back to page coordinates."""
    if factor == 1.0:
        return box
    return BoundingBox(
        x0=box.x0 / factor, y0=box.y0 / factor,
        x1=box.x1 / factor, y1=box.y1 / factor,
    )


def run(
    image: np.ndarray,
    *,
    scale_back: float = 1.0,
    config: str = DEFAULT_CONFIG,
) -> OcrResult:
    """Recognise an image, returning words with boxes and confidences.

    `scale_back` undoes any upscaling applied before OCR so that the boxes
    returned refer to the original page, which is what evidence crops need.
    """
    if not is_available():
        log.warning("tesseract not installed; OCR unavailable")
        return OcrResult()

    import pytesseract
    from pytesseract import Output

    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

    try:
        data = pytesseract.image_to_data(
            grey, config=config, output_type=Output.DICT
        )
    except Exception as exc:
        log.warning("ocr failed", error=str(exc)[:200])
        return OcrResult()

    words: list[Word] = []
    lines: dict[tuple[int, int, int], list[str]] = {}

    for i in range(len(data["text"])):
        token = data["text"][i].strip()
        if not token:
            continue

        raw_conf = float(data["conf"][i])
        if raw_conf < 0:
            continue  # Tesseract marks structural rows with -1.
        confidence = raw_conf / 100.0

        box = _scale_box(
            BoundingBox(
                x0=float(data["left"][i]),
                y0=float(data["top"][i]),
                x1=float(data["left"][i] + data["width"][i]),
                y1=float(data["top"][i] + data["height"][i]),
            ),
            scale_back,
        )
        words.append(Word(text=token, bbox=box, confidence=round(confidence, 4)))

        if confidence >= MIN_WORD_CONFIDENCE:
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append(token)

    text = "\n".join(" ".join(tokens) for _, tokens in sorted(lines.items()))
    scored = [w.confidence for w in words]
    mean = round(sum(scored) / len(scored), 4) if scored else 0.0

    return OcrResult(text=text, words=words, mean_confidence=mean)


def confidence_of_span(words: list[Word], needle: str) -> float | None:
    """Mean confidence over the words that make up `needle`.

    Lets a clause inherit the recognition quality of the exact text it quotes,
    rather than the page average — a figure read cleanly on an otherwise poor
    page should not be distrusted, and vice versa.
    """
    target = [t.lower().strip(".,:;()") for t in needle.split()]
    if not target or not words:
        return None

    lowered = [w.text.lower().strip(".,:;()") for w in words]
    for i in range(len(lowered) - len(target) + 1):
        if lowered[i : i + len(target)] == target:
            span = words[i : i + len(target)]
            return round(sum(w.confidence for w in span) / len(span), 4)
    return None
