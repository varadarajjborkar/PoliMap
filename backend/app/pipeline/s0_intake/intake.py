"""Stage 0 — turn an uploaded file into pages of text with provenance.

The routing decision is per page, not per document, because real uploads are
mixed: a PDF often carries a digitally generated schedule alongside a scanned
endorsement, and treating the whole file as one kind wastes accuracy on one half
or time on the other.

The ladder, in order of cost:

    native text layer  ->  free and exact
    OCR                ->  cheap, needs a straight, evenly lit page
    vision model       ->  slow and metered, but reads what OCR cannot
    ask the user       ->  last resort, and never silently

Each rung is only climbed when the one below it produced too little or scored
too low, so a clean PDF costs nothing and a bad photograph gets the full
treatment.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import fitz
import numpy as np

from app.agents.base import LLMUnavailable
from app.agents.registry import registry
from app.core.artifacts import page_dir
from app.core.config import ModelRole, settings
from app.core.events import bus
from app.core.logging import get_logger
from app.pipeline.s0_intake import ocr, preprocess
from app.schemas.document import (
    IngestedDocument,
    InputKind,
    Page,
    SourceMode,
    Word,
)
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.policy import BoundingBox

log = get_logger(__name__)

STAGE = PipelineStage.INTAKE

NATIVE_TEXT_MIN_CHARS = 180
"""Below this a PDF page is treated as scanned. A page carrying only a header
and a footer in its text layer is effectively an image."""

RASTER_DPI = 300
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

VISION_PROMPT = (
    "Transcribe every line of text visible in this document image, exactly as "
    "printed. Preserve the reading order and keep each line on its own line. "
    "Reproduce all numbers, currency amounts and percentages exactly as shown. "
    "Do not summarise, explain, correct, or add anything. Output only the "
    "transcription."
)


def _native_page(page: fitz.Page, index: int) -> Page:
    """Read a PDF page's own text layer, keeping word geometry."""
    words = [
        Word(
            text=w[4],
            bbox=BoundingBox(x0=w[0], y0=w[1], x1=w[2], y1=w[3]),
            confidence=1.0,
        )
        for w in page.get_text("words")
    ]
    return Page(
        page_index=index,
        width=page.rect.width,
        height=page.rect.height,
        text=page.get_text().strip(),
        words=words,
        source_mode=SourceMode.NATIVE,
    )


def _rasterize(page: fitz.Page, dpi: int = RASTER_DPI) -> np.ndarray:
    pix = page.get_pixmap(dpi=dpi)
    buf = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        return cv2.cvtColor(buf, cv2.COLOR_RGBA2BGR)
    if pix.n == 3:
        return cv2.cvtColor(buf, cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(buf, cv2.COLOR_GRAY2BGR)


def _escalate_to_vision(image: np.ndarray, index: int, session_id: str | None) -> str:
    """Ask a vision model to read a page OCR could not."""
    ok, buf = cv2.imencode(".png", image)
    if not ok:
        return ""
    try:
        response = registry.complete(
            ModelRole.VISION_OCR,
            prompt=VISION_PROMPT,
            images=[buf.tobytes()],
            temperature=0.0,
        )
    except LLMUnavailable as exc:
        bus.publish(
            STAGE, "vision_escalation", status=EventStatus.SKIPPED,
            summary="No vision model available; keeping the OCR result",
            session_id=session_id, page=index, reason=str(exc)[:160],
        )
        return ""
    return response.text.strip()


def _ocr_page(
    image: np.ndarray,
    index: int,
    session_id: str | None,
    *,
    source_dpi: int,
    aggressive: bool,
) -> Page:
    """Preprocess, recognise, and escalate to a vision model if needed."""
    height, width = image.shape[:2]

    prep = preprocess.prepare(image, source_dpi=source_dpi, aggressive=aggressive)
    result = ocr.run(prep.image, scale_back=prep.upscaled)

    page = Page(
        page_index=index,
        width=float(width),
        height=float(height),
        text=result.text,
        words=result.words,
        source_mode=SourceMode.OCR if result.char_count else SourceMode.EMPTY,
        rotation_corrected_deg=prep.rotation_applied_deg,
    )

    bus.publish(
        STAGE, "ocr_page",
        status=EventStatus.OK if result.char_count else EventStatus.WARN,
        summary=(
            f"Page {index + 1}: read {result.char_count} characters "
            f"at {result.mean_confidence:.0%} confidence"
        ),
        session_id=session_id,
        page=index,
        chars=result.char_count,
        confidence=result.mean_confidence,
        preprocessing=prep.steps,
    )

    needs_help = (
        result.mean_confidence < settings.ocr_confidence_threshold
        or result.char_count < NATIVE_TEXT_MIN_CHARS
    )
    if not needs_help:
        return page

    with bus.step(
        STAGE, "vision_escalation", session_id=session_id, page=index,
        summary=(
            f"Page {index + 1} scored {result.mean_confidence:.0%}; "
            f"asking a vision model to read it"
        ),
    ) as step:
        transcript = _escalate_to_vision(prep.image, index, session_id)
        if len(transcript) > result.char_count:
            page.text = transcript
            page.source_mode = SourceMode.VISION
            page.escalated = True
            # A vision transcript has no word geometry. The OCR boxes are kept
            # so evidence crops still work, but confidence is now the model's,
            # not Tesseract's, and is deliberately not claimed as exact.
            step.ok(
                f"Vision model recovered {len(transcript)} characters",
                chars=len(transcript), replaced_ocr=True,
            )
        else:
            step.warn(
                "Vision pass added nothing; keeping the OCR result",
                chars=len(transcript), replaced_ocr=False,
            )

    return page


def ingest(
    path: Path,
    *,
    session_id: str | None = None,
    save_page_images: bool = True,
) -> IngestedDocument:
    """Read a file into pages of text, choosing a strategy per page."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in IMAGE_SUFFIXES:
        return _ingest_image(path, session_id=session_id, save_page_images=save_page_images)
    return _ingest_pdf(path, session_id=session_id, save_page_images=save_page_images)


def _ingest_image(
    path: Path, *, session_id: str | None, save_page_images: bool
) -> IngestedDocument:
    with bus.step(
        STAGE, "read_image", session_id=session_id,
        summary=f"Reading {path.name}",
    ) as step:
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Could not read image: {path.name}")

        # A photo carries no trustworthy DPI metadata, so it is inferred from
        # the page dimensions. Assuming a fixed low value upscales an already
        # high-resolution capture past the range Tesseract handles well.
        source_dpi = preprocess.estimate_dpi(image)
        page = _ocr_page(image, 0, session_id, source_dpi=source_dpi, aggressive=True)
        if save_page_images:
            out = page_dir(session_id) / f"{path.stem}_p0.png"
            cv2.imwrite(str(out), image)
            page.image_path = str(out)

        step.ok(
            f"Read {page.char_count} characters from the photo",
            chars=page.char_count, confidence=page.mean_confidence,
        )

    document = IngestedDocument(
        filename=path.name, input_kind=InputKind.IMAGE,
        pages=[page], session_id=session_id,
    )
    _warn_if_poor(document)
    return document


def _ingest_pdf(
    path: Path, *, session_id: str | None, save_page_images: bool
) -> IngestedDocument:
    pages: list[Page] = []
    scanned_pages = 0

    with fitz.open(path) as doc:
        page_count = doc.page_count
        bus.publish(
            STAGE, "open_pdf", session_id=session_id,
            summary=f"Opened {path.name} — {page_count} page"
                    f"{'s' if page_count != 1 else ''}",
            pages=page_count,
        )

        for index, pdf_page in enumerate(doc):
            native = _native_page(pdf_page, index)

            if native.char_count >= NATIVE_TEXT_MIN_CHARS:
                bus.publish(
                    STAGE, "native_text", session_id=session_id,
                    summary=f"Page {index + 1}: used the PDF's own text layer "
                            f"({native.char_count} characters)",
                    page=index, chars=native.char_count,
                )
                pages.append(native)
                continue

            # Too little text to be a real text layer — treat it as an image.
            scanned_pages += 1
            image = _rasterize(pdf_page)
            page = _ocr_page(
                image, index, session_id, source_dpi=RASTER_DPI, aggressive=True
            )
            page.width, page.height = pdf_page.rect.width, pdf_page.rect.height

            if save_page_images:
                out = page_dir(session_id) / f"{path.stem}_p{index}.png"
                cv2.imwrite(str(out), image)
                page.image_path = str(out)
            pages.append(page)

    document = IngestedDocument(
        filename=path.name,
        input_kind=InputKind.PDF_SCANNED if scanned_pages else InputKind.PDF_TEXT,
        pages=pages,
        session_id=session_id,
    )

    bus.publish(
        STAGE, "intake_complete", session_id=session_id,
        summary=(
            f"{path.name}: {len(pages)} pages, {document.total_chars} characters, "
            f"quality {document.quality_score:.0%}"
        ),
        input_kind=document.input_kind.value,
        scanned_pages=scanned_pages,
        quality=document.quality_score,
    )
    _warn_if_poor(document)
    return document


def _warn_if_poor(document: IngestedDocument) -> None:
    """Record quality problems on the document so the UI can be honest.

    A user who uploaded an unreadable photo should be told to retake it, not
    handed a confident answer derived from nothing.
    """
    if not document.is_usable:
        document.warnings.append(
            "We could not read enough text from this file. "
            "Try a clearer photo, or enter your details manually."
        )
        return

    if document.quality_score < 0.60:
        document.warnings.append(
            "This document was hard to read, so some details may be wrong. "
            "Please check the figures we show you."
        )

    unreadable = [p.page_index + 1 for p in document.pages if not p.is_legible]
    if unreadable and len(unreadable) < document.page_count:
        document.warnings.append(
            f"We could not read page{'s' if len(unreadable) > 1 else ''} "
            f"{', '.join(map(str, unreadable))}."
        )


def ingest_bytes(
    data: bytes, filename: str, *, session_id: str | None = None
) -> IngestedDocument:
    """Ingest an uploaded payload held in memory."""
    suffix = Path(filename).suffix.lower() or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    try:
        document = ingest(temp_path, session_id=session_id)
        document.filename = filename
        return document
    finally:
        temp_path.unlink(missing_ok=True)
