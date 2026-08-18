"""Finding a font that can draw a rupee sign.

reportlab's built-in Helvetica has no ₹ glyph, and neither do several faces that
look like safe bets: Arial Unicode predates the sign's introduction in 2010 and
emits NUL for it silently. Registering a font therefore proves nothing, so the
character map is inspected directly.

Candidates are listed Linux-first, so a deploy box resolves without depending on
whatever happens to be installed on a developer's machine. Where none covers the
glyph, callers fall back to "Rs.", which is what most Indian policy documents
print anyway.

Lives here rather than beside either of the two things that render PDFs, because
this is subtle enough that two copies of it would drift.
"""

from __future__ import annotations

from pathlib import Path

RUPEE_CODEPOINT = 0x20B9

_FONT_CANDIDATES: list[tuple[str, str, str]] = [
    ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("NotoSans", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
     "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ("Georgia", "/System/Library/Fonts/Supplemental/Georgia.ttf",
     "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
    ("Geneva", "/System/Library/Fonts/Geneva.ttf", ""),
]


def _covers_rupee(path: str) -> bool:
    from reportlab.pdfbase.ttfonts import TTFont

    try:
        return RUPEE_CODEPOINT in TTFont("probe", path).face.charToGlyph
    except Exception:
        return False


def resolve() -> tuple[str, str, bool]:
    """Return (regular font name, bold font name, whether ₹ can be drawn)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for name, regular, bold in _FONT_CANDIDATES:
        if not Path(regular).exists() or not _covers_rupee(regular):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, regular))
            if bold and Path(bold).exists() and _covers_rupee(bold):
                pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                return name, f"{name}-Bold", True
            # A single-weight face still beats losing the glyph.
            return name, name, True
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold", False
