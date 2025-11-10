"""Test helpers for Kaizen SDK."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # pragma: no cover - import-time side effect
    sys.path.insert(0, str(ROOT))
