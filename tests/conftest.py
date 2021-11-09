from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

import ufoLib2


@pytest.fixture
def datadir(request: Any) -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture
def ufo_UbuTestData(tmp_path: Path, datadir: Path) -> ufoLib2.Font:
    ufo_path = tmp_path / "UbuTestData.ufo"
    shutil.copytree(datadir / "UbuTestData.ufo", ufo_path)
    return ufoLib2.Font.open(ufo_path)
