"""Dataset builders.

The problem statement requires synthetic or user-provided mock data for
insurance, and publicly available or simulated data for hospitals. Everything
here is generated, but generated *from real anchors*: real localities and
coordinates, CGHS-published package rates, and the accreditation tiers Indian
pricing actually keys off. That keeps the figures defensible without depending
on a live portal or scraping anyone.

Run `python -m datagen.build_all` from the repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Let the builders import the domain schemas without an install step.
_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))