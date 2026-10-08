from __future__ import annotations

import json
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

import attrs
import pytest

import ufoLib2.objects
from ufoLib2.constants import DATA_LIB_KEY, DATE_LIB_KEY
from ufoLib2.objects.info import GaspRangeRecord, Info, NameRecord, woff

# isort: off
pytest.importorskip("cattrs")
jsonschema = pytest.importorskip("jsonschema")

import ufoLib2.serde.json  # noqa: E402


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    text = resources.files("ufoLib2.serde").joinpath("font.schema.json").read_text()
    data: dict[str, Any] = json.loads(text)
    jsonschema.Draft202012Validator.check_schema(data)
    return data


@pytest.fixture(scope="module")
def validator(schema: dict[str, Any]) -> Any:
    return jsonschema.Draft202012Validator(schema)


@pytest.mark.parametrize("have_orjson", [False, True], ids=["no-orjson", "with-orjson"])
@pytest.mark.parametrize(
    "ufo", ["UbuTestData.ufo", "MutatorSansBoldCondensed.ufo", "WoffMetadataTest.ufo"]
)
def test_dumped_fonts_are_valid(
    datadir: Path, validator: Any, ufo: str, monkeypatch: Any, have_orjson: bool
) -> None:
    if not have_orjson:
        monkeypatch.setattr(ufoLib2.serde.json, "have_orjson", have_orjson)
    else:
        pytest.importorskip("orjson")

    font = ufoLib2.Font.open(datadir / ufo)
    font.images["image.png"] = b"\x89PNG"
    font.data["com.example/blob.bin"] = b"\0"
    font.lib["com.example.bytes"] = [b"\1"]
    font.lib["com.example.date"] = datetime(2020, 1, 2, 3, 4, 5)
    font.layers.defaultLayer.lib["com.example.bytes"] = b"\2"
    font.layers.defaultLayer.tempLib["com.example.nested"] = {"a": [{"b": b"\3"}]}
    font.layers.defaultLayer.color = "1,0,0,1"
    validator.validate(json.loads(font.json_dumps()))  # type: ignore


def test_committed_json_is_valid(datadir: Path, validator: Any) -> None:
    validator.validate(
        json.loads((datadir / "MutatorSansBoldCondensed.json").read_text())
    )


@pytest.mark.parametrize(
    "path, value",
    [
        (("unknownKey",), 1),
        (("layers", 0, "glyphs", "a", "unknownKey"), 1),
        (("layers", 0, "glyphs", "a", "contours", 0, "points", 0, "x"), "1"),
        (("layers", 0, "glyphs", "a", "components", 0, "transformation"), [1, 0]),
        (("layers", 0, "glyphs", "a", "guidelines", 0, "angle"), 361),
        (("info", "openTypeOS2WeightClass"), 0),
        (("kerning", "a", "b"), "10"),
        (("info", "woffMetadataDescription"), {}),
        (("lib", "null"), None),
        (("lib", "data", "data"), 5),
        (("lib", "data", "data"), "A"),
        (("lib", "nested", 0, "date", "date"), 5),
        (("lib", "nested", 0, "date", "date"), "2020-01-02"),
        (("lib", "nested", 0, "date", "extra"), 1),
        (("layers", 0, "lib"), {"x": {"y": [None]}}),
        (("layers", 0, "name"), "background"),
        (("layers",), [{"name": "public.default"}, {"name": "b", "default": True}]),
    ],
)
def test_invalid(validator: Any, path: tuple[Any, ...], value: Any) -> None:
    doc: dict[str, Any] = {
        "layers": [
            {
                "name": "public.default",
                "glyphs": {
                    "a": {
                        "contours": [{"points": [{"x": 0, "y": 0, "type": "move"}]}],
                        "components": [{"baseGlyph": "b"}],
                        "guidelines": [{"x": 0, "y": 0, "angle": 0}],
                    }
                },
            }
        ],
        "info": {
            "openTypeOS2WeightClass": 400,
            "woffMetadataDescription": {"text": [{"text": "x"}]},
        },
        "kerning": {"a": {"b": 10}},
        "lib": {
            "data": {"type": DATA_LIB_KEY, "data": "AAE="},
            "nested": [
                {"date": {"type": DATE_LIB_KEY, "date": "2020-01-02T03:04:05Z"}}
            ],
            # not wrappers: plain dictionaries
            "other": {"type": "other", "data": 5},
            "half": {"type": DATE_LIB_KEY, "data": 5},
        },
    }
    validator.validate(doc)
    parent = doc
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    assert not validator.is_valid(doc)


def _json_keys(cls: type[Any]) -> set[str]:
    # mirrors the renaming rule in ufoLib2.converters.register_hooks
    return {
        a.metadata.get("rename_attr", a.name[1:] if a.name[0] == "_" else a.name)
        for a in attrs.fields(cls)
        if a.init
    }


@pytest.mark.parametrize(
    "cls, definition",
    [
        (ufoLib2.objects.Anchor, "anchor"),
        (ufoLib2.objects.Component, "component"),
        (ufoLib2.objects.Contour, "contour"),
        (ufoLib2.objects.Glyph, "glyph"),
        (ufoLib2.objects.Guideline, "guideline"),
        (ufoLib2.objects.Image, "image"),
        (ufoLib2.objects.Point, "point"),
        (Info, "info"),
        (GaspRangeRecord, "gaspRangeRecord"),
        (NameRecord, "nameRecord"),
    ],
)
def test_schema_matches_attrs_fields(
    schema: dict[str, Any], cls: type[Any], definition: str
) -> None:
    assert set(schema["$defs"][definition]["properties"]) == _json_keys(cls)


def test_woff_definitions_match_attrs_fields(schema: dict[str, Any]) -> None:
    classes = [
        v
        for k, v in vars(woff).items()
        if k.startswith("WoffMetadata") and attrs.has(v)
    ]
    assert classes
    for cls in classes:
        name = cls.__name__[0].lower() + cls.__name__[1:]
        assert set(schema["$defs"][name]["properties"]) == _json_keys(cls), name


def test_font_and_layer_keys(schema: dict[str, Any]) -> None:
    assert set(schema["properties"]) == _json_keys(ufoLib2.objects.Font)
    layer = ufoLib2.objects.Layer(
        name="foo", default=True, color="0,0,0,1", lib={"a": 1}, tempLib={"b": 2}
    )
    layer.newGlyph("a")
    unstructured = json.loads(ufoLib2.objects.Font(layers=[layer]).json_dumps())  # type: ignore
    assert set(unstructured["layers"][0]) == set(schema["$defs"]["layer"]["properties"])
