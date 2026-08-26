"""Bring the app mark into the palette the rest of the interface uses.

The mark was drawn in blues and teals while the application is built on a deep
green, so on the header it read as something borrowed from another product. This
rotates the cool half of the mark onto the brand's own hue and leaves the amber
accent alone, which is the one part that is meant to stand apart.

Every size is regenerated from the 512px master, so the favicon, the manifest
icons and the inline mark in the README cannot drift out of step with each
other.

    python scripts/recolour_logo.py

Idempotent in the sense that matters: it always reads `SOURCE` and rewrites the
derived sizes, so running it twice does not compound the rotation.
"""

from __future__ import annotations

import colorsys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "logo-master.png"
PUBLIC = ROOT / "frontend" / "public"
DOCS = ROOT / "docs" / "images"

# The cool band to move, in degrees. Everything outside it, notably the amber,
# is left exactly as drawn.
COOL_FROM, COOL_TO = 150.0, 265.0

# Where that band lands. The brand green is #0f5c4a, which sits at 166 degrees,
# so the range is compressed around it rather than rotated rigidly: a rigid
# rotation keeps the original spread and the mark comes out as several
# unrelated greens instead of one family.
TARGET_FROM, TARGET_TO = 138.0, 176.0

SATURATION_LIFT = 1.08
"""Greens read flatter than blues at the same saturation. A small lift keeps the
mark from going grey once it has moved."""

SIZES = {
    PUBLIC / "logo-512.png": 512,
    PUBLIC / "logo-192.png": 192,
    PUBLIC / "logo-64.png": 64,
    PUBLIC / "apple-touch-icon.png": 180,
    PUBLIC / "favicon-32.png": 32,
    PUBLIC / "favicon-16.png": 16,
    DOCS / "logo-inline.png": 64,
}


def shift_hue(image: Image.Image) -> Image.Image:
    out = image.convert("RGBA")
    pixels = out.load()
    assert pixels is not None

    width, height = out.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue

            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            degrees = h * 360

            if not (COOL_FROM <= degrees <= COOL_TO):
                continue

            position = (degrees - COOL_FROM) / (COOL_TO - COOL_FROM)
            moved = TARGET_FROM + position * (TARGET_TO - TARGET_FROM)

            nr, ng, nb = colorsys.hsv_to_rgb(
                moved / 360, min(s * SATURATION_LIFT, 1.0), v
            )
            pixels[x, y] = (
                round(nr * 255), round(ng * 255), round(nb * 255), a
            )

    return out


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(
            f"{SOURCE} not found. It is the untouched master the sizes are cut "
            f"from; without it a second run would rotate an already rotated mark."
        )

    master = shift_hue(Image.open(SOURCE))

    for path, size in SIZES.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        master.resize((size, size), Image.LANCZOS).save(path, optimize=True)
        print(f"  wrote {path.relative_to(ROOT)}  ({size}px)")

    # The .ico carries several sizes in one file, which is what Windows and a
    # few feed readers still ask for.
    master.resize((64, 64), Image.LANCZOS).save(
        PUBLIC / "favicon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )
    print(f"  wrote {(PUBLIC / 'favicon.ico').relative_to(ROOT)}  (multi-size)")


if __name__ == "__main__":
    main()