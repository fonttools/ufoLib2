from pathlib import Path

import pytest

import ufoLib2.objects

# isort: off
pytest.importorskip("cattrs")
pytest.importorskip("msgpack")

import msgpack  # type: ignore  # noqa

import ufoLib2.serde.msgpack  # noqa: E402


def test_dumps_loads(ufo_UbuTestData: ufoLib2.objects.Font) -> None:
    font = ufo_UbuTestData
    data = font.msgpack_dumps()  # type: ignore

    assert data[:10] == b"\x85\xa6layers\x92\x82"

    font2 = ufoLib2.objects.Font.msgpack_loads(data)  # type: ignore

    assert font == font2


def test_dump_load(tmp_path: Path, ufo_UbuTestData: ufoLib2.objects.Font) -> None:
    font = ufo_UbuTestData
    with open(tmp_path / "test.msgpack", "wb") as f:
        font.msgpack_dump(f)  # type: ignore

    with open(tmp_path / "test.msgpack", "rb") as f:
        font2 = ufoLib2.objects.Font.msgpack_load(f)  # type: ignore

    assert font == font2

    # laod/dump work with paths too, not just file objects
    font3 = ufoLib2.objects.Font.msgpack_load(tmp_path / "test.msgpack")  # type: ignore

    assert font == font3

    font.msgpack_dump(tmp_path / "test2.msgpack")  # type: ignore

    assert (tmp_path / "test.msgpack").read_bytes() == (
        tmp_path / "test2.msgpack"
    ).read_bytes()


def test_allow_bytes(ufo_UbuTestData: ufoLib2.objects.Font) -> None:
    font = ufo_UbuTestData

    # DataSet values are binary data (bytes)
    assert all(isinstance(v, bytes) for v in font.data.values())

    # bytes *are* allowed in MessagePack (unlike JSON), so its converter should
    # keep them as such (not translate them to Base64 str) upon serializig
    b = font.data.msgpack_dumps()  # type: ignore

    # check that (even before structuring the DataSet object) the msgpack raw data
    # contains in fact bytes, not str
    raw_data = msgpack.unpackb(b)
    assert isinstance(raw_data, dict)
    assert all(isinstance(v, bytes) for v in raw_data.values())

    # of course, also after structuring, the DataSet should contain bytes
    data = font.data.msgpack_loads(b)  # type: ignore
    assert isinstance(data, ufoLib2.objects.DataSet)
    assert all(isinstance(v, bytes) for v in data.values())
