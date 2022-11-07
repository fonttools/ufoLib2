from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import ufoLib2.objects

# isort: off
pytest.importorskip("cattrs")

import ufoLib2.serde.json  # noqa: E402


@pytest.mark.parametrize("have_orjson", [False, True], ids=["no-orjson", "with-orjson"])
def test_dumps_loads(
    monkeypatch: Any, have_orjson: bool, ufo_UbuTestData: ufoLib2.objects.Font
) -> None:
    if not have_orjson:
        monkeypatch.setattr(ufoLib2.serde.json, "have_orjson", have_orjson)
    else:
        pytest.importorskip("orjson")

    font = ufo_UbuTestData
    data = font.json_dumps()  # type: ignore

    assert isinstance(data, bytes)

    if have_orjson:
        # with default indent=0, orjson adds no space between keys and values
        assert data[:21] == b'{"layers":[{"name":"p'
    else:
        # built-in json always adds space between keys and values
        assert data[:21] == b'{"layers": [{"name": '

    font2 = ufoLib2.objects.Font.json_loads(data)  # type: ignore

    assert font == font2


@pytest.mark.parametrize("have_orjson", [False, True], ids=["no-orjson", "with-orjson"])
@pytest.mark.parametrize("indent", [None, 2], ids=["no-indent", "indent-2"])
@pytest.mark.parametrize("sort_keys", [False, True], ids=["no-sort-keys", "sort-keys"])
def test_dump_load(
    monkeypatch: Any,
    tmp_path: Path,
    ufo_UbuTestData: ufoLib2.objects.Font,
    have_orjson: bool,
    indent: int | None,
    sort_keys: bool,
) -> None:
    if not have_orjson:
        monkeypatch.setattr(ufoLib2.serde.json, "have_orjson", have_orjson)

    font = ufo_UbuTestData
    with open(tmp_path / "test.json", "wb") as f:
        font.json_dump(f, indent=indent, sort_keys=sort_keys)  # type: ignore

    with open(tmp_path / "test.json", "rb") as f:
        font2 = ufoLib2.objects.Font.json_load(f)  # type: ignore

    assert font == font2

    with open(tmp_path / "test.json", "wb") as f:
        font.json_dump(f, indent=indent, sort_keys=sort_keys)  # type: ignore

    # load/dump work with paths too, not just file objects
    font3 = ufoLib2.objects.Font.json_load(tmp_path / "test.json")  # type: ignore

    assert font == font3

    font.json_dump(  # type: ignore
        tmp_path / "test2.json",
        indent=indent,
        sort_keys=sort_keys,
    )

    assert (tmp_path / "test.json").read_bytes() == (
        tmp_path / "test2.json"
    ).read_bytes()


@pytest.mark.parametrize("indent", [1, 3], ids=["indent-1", "indent-3"])
def test_indent_not_2_orjson(indent: int) -> None:
    pytest.importorskip("orjson")
    with pytest.raises(ValueError):
        ufoLib2.serde.json.dumps(None, indent=indent)


def test_not_allow_bytes(ufo_UbuTestData: ufoLib2.objects.Font) -> None:
    font = ufo_UbuTestData

    # DataSet values are binary data (bytes)
    assert all(isinstance(v, bytes) for v in font.data.values())

    # bytes are are not allowed in JSON, so our converter automatically
    # translates them to Base64 strings upon serializig
    s = font.data.json_dumps()  # type: ignore

    # check that (before structuring the DataSet object) the json data
    # contains in fact str, not bytes
    raw_data = json.loads(s)
    assert isinstance(raw_data, dict)
    assert all(isinstance(v, str) for v in raw_data.values())

    # check that (after structuring the DataSet object) the json data
    # now contains bytes, like the original data
    data = font.data.json_loads(s)  # type: ignore
    assert isinstance(data, ufoLib2.objects.DataSet)
    assert all(isinstance(v, bytes) for v in data.values())
