"""Shared pytest configuration for the MiloOS test suite.

The core engines live in nested directories and are normally launched as
scripts, not imported as packages. Put their directories on sys.path so the
tests can import them directly from the working tree.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for relative in ("core/evolution", "core/cortex"):
    candidate = str(ROOT / relative)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)
