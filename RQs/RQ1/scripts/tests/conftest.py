from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
for path in (ROOT / "RQs", SCRIPTS):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)
