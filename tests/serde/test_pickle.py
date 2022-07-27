import pickle
from pathlib import Path
from typing import Any

import pytest

import ufoLib2.objects
import ufoLib2.serde.pickle


@pytest.fixture
def font(request: Any, datadir: Path) -> ufoLib2.Font:
    lazy = request.param
    if lazy is not None:
        return ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=lazy)
    else:
        return ufoLib2.Font.open(datadir / "UbuTestData.ufo")


@pytest.mark.parametrize(
    "font", [None, False, True], ids=["lazy-unset", "non-lazy", "lazy"], indirect=True
)
def test_dumps_loads(font: ufoLib2.objects.Font) -> None:
    orig_lazy = font._lazy

    data = font.pickle_dumps()  # type: ignore

    assert isinstance(data, bytes) and len(data) > 0

    # picklying unlazifies
    if orig_lazy:
        assert font._lazy is False
    else:
        assert font._lazy is orig_lazy

    font2 = ufoLib2.objects.Font.pickle_loads(data)  # type: ignore

    assert font == font2
    # unpickling doesn't initialize the lazy flag, which resets to default
    assert font2._lazy is None

    # Font.pickle_loads(s) is just syntactic sugar for pickle.loads(s) anyway
    font3 = pickle.loads(data)
    assert font == font3
    # same for font.pickle_dumps() => pickle.dumps(font)
    assert data == pickle.dumps(font3)


@pytest.mark.parametrize(
    "font", [None, False, True], ids=["lazy-unset", "non-lazy", "lazy"], indirect=True
)
def test_dump_load(tmp_path: Path, font: ufoLib2.objects.Font) -> None:
    with open(tmp_path / "test.pickle", "wb") as f:
        font.pickle_dump(f)  # type: ignore

    with open(tmp_path / "test.pickle", "rb") as f:
        font2 = ufoLib2.objects.Font.pickle_load(f)  # type: ignore

    assert font == font2
