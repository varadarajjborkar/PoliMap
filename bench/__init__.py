"""Benchmarks.

Run from the repository root:

    python -m bench.ocr_bench       # intake quality by document condition
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
