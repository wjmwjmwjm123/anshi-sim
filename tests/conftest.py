"""Project-local pytest temp directory to avoid Windows %TEMP% permission issues."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


_PROJECT_ROOT = Path(__file__).parent.parent
_LOCAL_TEMP = _PROJECT_ROOT / ".pytest_tmp"
_LOCAL_TEMP.mkdir(exist_ok=True)


@pytest.fixture
def tmp_path() -> Path:
    """Override pytest's tmp_path to use a project-local temporary directory."""
    with tempfile.TemporaryDirectory(dir=_LOCAL_TEMP, prefix="test-") as path:
        yield Path(path)
