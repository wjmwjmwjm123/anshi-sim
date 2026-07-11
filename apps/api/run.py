from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    uvicorn.run("apps.api.main:app", host="127.0.0.1", port=8000)
