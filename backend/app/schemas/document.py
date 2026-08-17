"""Ingested document representation.

Everything the pipeline later claims about a policy has to be traceable back to
a place on a page. These types carry that trail: each word keeps its bounding
box and, when it came from OCR, its recognition confidence. That is what lets
the interface show a user the exact patch of their own document a number was
read from, which matters more here than in most extraction problems, because
the user is being asked to confirm figures they may not understand.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

from app.schemas.policy import BoundingBox, DocumentSection


class SourceMode(StrEnum):
    """How a page's text was obtained."""

    NATIVE = "native"
    """Extracted from the PDF's own text layer. Exact, no recognition error."""
    OCR = "ocr"
    """Recognised from pixels by the OCR engine."""
    VISION = "vision"
    """Transcribed by a vision model after OCR confidence came out too low."""
    EMPTY = "empty"
    """Nothing legible was recovered."""


class InputKind(StrEnum):
    PDF_TEXT = "pdf_text"
    PDF_SCANNED = "pdf_scanned"
    IMAGE = "image"

    @property
    def label(self) -> str:
        return {
            InputKind.PDF_TEXT: "PDF with selectable text",
            InputKind.PDF_SCANNED: "Scanned PDF (images only)",
            InputKind.IMAGE: "Photo or image",
        }[self]


class Word(BaseModel):
    """One recognised token and where it sits on the page."""

    text: str
    bbox: BoundingBox
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Page(BaseModel):
    page_index: int = Field(ge=0)
    width: float
    height: float
    text: str = ""
    words: list[Word] = Field(default_factory=list)
    source_mode: SourceMode = SourceMode.EMPTY
    image_path: str | None = None
    """Rendered page image, kept so evidence crops can be produced later."""

    rotation_corrected_deg: float = 0.0
    section: DocumentSection = DocumentSection.UNKNOWN
    escalated: bool = False
    """Whether this page needed a vision pass beyond OCR."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def char_count(self) -> int:
        return len(self.text.strip())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mean_confidence(self) -> float:
        """Mean word confidence. 1.0 for native text, which has no error."""
        if self.source_mode is SourceMode.NATIVE:
            return 1.0
        scored = [w.confidence for w in self.words if w.text.strip()]
        return round(sum(scored) / len(scored), 4) if scored else 0.0

    @property
    def is_legible(self) -> bool:
        return self.char_count > 40

    def crop_for(self, bbox: BoundingBox, pad: float = 8.0) -> BoundingBox:
        """Clamp a padded crop box to the page, for showing evidence."""
        padded = bbox.padded(pad)
        return BoundingBox(
            x0=max(0.0, padded.x0),
            y0=max(0.0, padded.y0),
            x1=min(self.width, padded.x1),
            y1=min(self.height, padded.y1),
        )

    def find_span(self, needle: str) -> tuple[int, int] | None:
        """Character offsets of `needle` in this page's text."""
        start = self.text.find(needle)
        return (start, start + len(needle)) if start >= 0 else None

    def bbox_for_span(self, needle: str) -> BoundingBox | None:
        """Union of the boxes of the words making up `needle`.

        Matched over the word sequence rather than the flat text, because the
        flat text is a reconstruction and its offsets do not map back to pixels.
        """
        target = needle.split()
        if not target or not self.words:
            return None

        lowered = [w.text.lower().strip(".,:;()") for w in self.words]
        wanted = [t.lower().strip(".,:;()") for t in target]

        for i in range(len(lowered) - len(wanted) + 1):
            if lowered[i : i + len(wanted)] == wanted:
                box = self.words[i].bbox
                for word in self.words[i + 1 : i + len(wanted)]:
                    box = box.union(word.bbox)
                return box
        return None


class IngestedDocument(BaseModel):
    """A document after intake, ready for triage and extraction."""

    document_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    filename: str
    input_kind: InputKind
    pages: list[Page] = Field(default_factory=list)
    session_id: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def page_count(self) -> int:
        return len(self.pages)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_chars(self) -> int:
        return sum(p.char_count for p in self.pages)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def quality_score(self) -> float:
        """Overall confidence in what was read, weighted by page length.

        Length-weighted because a near-empty page recognised perfectly should
        not offset a dense page recognised badly.
        """
        pages = [p for p in self.pages if p.char_count]
        if not pages:
            return 0.0
        total = sum(p.char_count for p in pages)
        return round(
            sum(p.mean_confidence * p.char_count for p in pages) / total, 4
        )

    @property
    def needed_ocr(self) -> bool:
        return any(p.source_mode in (SourceMode.OCR, SourceMode.VISION) for p in self.pages)

    @property
    def is_usable(self) -> bool:
        return any(p.is_legible for p in self.pages)

    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)

    def page(self, index: int) -> Page | None:
        return next((p for p in self.pages if p.page_index == index), None)
