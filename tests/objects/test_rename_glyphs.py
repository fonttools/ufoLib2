from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from ufoLib2 import Font
from ufoLib2.objects import Component, Layer
from ufoLib2.objects.layer import _GLYPH_NOT_LOADED


def make_layer() -> Layer:
    layer = Layer()
    for name in ("a", "b", "c", "composite", "nested"):
        glyph = layer.newGlyph(name)
        glyph.width = 100 + len(name)
    layer["composite"].components.extend(
        [Component("a"), Component("b"), Component("a", (1, 0, 0, 1, 10, 20))]
    )
    layer["nested"].components.append(Component("composite"))
    return layer


def component_names(layer: Layer, name: str) -> list[str]:
    return [component.baseGlyph for component in layer[name].components]


def test_batch_renames_component_references_once() -> None:
    layer = make_layer()
    original = dict((glyph.name, glyph) for glyph in layer)
    keys = layer.keys()
    transform = layer["composite"].components[2].transformation
    layer.renameGlyphs({"a": "b", "b": "c", "c": "d", "composite": "combined"})

    assert set(keys) == {"b", "c", "d", "combined", "nested"}
    assert layer["b"] is original["a"]
    assert layer["c"] is original["b"]
    assert layer["d"] is original["c"]
    assert layer["combined"] is original["composite"]
    assert component_names(layer, "combined") == ["b", "c", "b"]
    assert component_names(layer, "nested") == ["combined"]
    assert layer["combined"].components[2].transformation == transform


def test_batch_shared_component_objects_are_renamed_once() -> None:
    layer = make_layer()
    shared = Component("a", (1, 0, 0, 1, 10, 20))
    distinct = Component("a")
    layer["composite"].components[:] = [shared, shared, distinct]
    layer["nested"].components[:] = [shared]
    layer.renameGlyphs({"a": "b", "b": "a"})

    assert component_names(layer, "composite") == ["b", "b", "b"]
    assert component_names(layer, "nested") == ["b"]
    assert layer["composite"].components[0] is shared
    assert layer["composite"].components[1] is shared
    assert layer["nested"].components[0] is shared
    assert layer["composite"].components[2] is distinct
    assert shared.transformation == (1, 0, 0, 1, 10, 20)


@pytest.mark.parametrize(
    "mapping", [{"a": "b", "b": "a"}, {"a": "b", "b": "c", "c": "a"}]
)
def test_batch_rename_cycles(mapping: dict[str, str]) -> None:
    layer = make_layer()
    original = {name: layer[name] for name in mapping}
    layer.renameGlyphs(mapping)
    for name, new_name in mapping.items():
        assert layer[new_name] is original[name]
        assert layer[new_name].name == new_name
    assert component_names(layer, "composite") == [
        mapping["a"],
        mapping["b"],
        mapping["a"],
    ]


@pytest.mark.parametrize(
    "mapping,overwrite,error",
    [
        ({"a": "new", "missing": "also-new"}, False, KeyError),
        ({"a": "new", "b": "c"}, False, KeyError),
        ({"a": "same", "b": "same"}, False, ValueError),
        ({"a": "same", "b": "same"}, True, ValueError),
        ({"a": "a", "b": "a"}, True, ValueError),
        ({"missing": "missing"}, False, KeyError),
        ({"a": 1}, False, TypeError),
    ],
)
def test_invalid_batch_has_no_partial_changes(
    mapping: dict[str, Any], overwrite: bool, error: type[Exception]
) -> None:
    layer = make_layer()
    before = deepcopy(layer)
    with pytest.raises(error):
        layer.renameGlyphs(mapping, overwrite=overwrite)
    assert layer == before


def test_batch_overwrite_retains_source_and_updates_components() -> None:
    layer = make_layer()
    original = layer["a"]
    replaced = layer["b"]
    layer.renameGlyphs({"a": "b"}, overwrite=True)
    assert "a" not in layer
    assert layer["b"] is original
    assert replaced.name == "b"
    assert component_names(layer, "composite") == ["b", "b", "b"]


def test_identity_entries_preserve_glyphs() -> None:
    layer = make_layer()
    original = layer["a"]
    layer.renameGlyphs({"a": "a", "b": "new"})
    assert layer["a"] is original
    assert component_names(layer, "composite") == ["a", "new", "a"]


def test_batch_font_default_layer_and_explicit_other_layer(tmp_path: Path) -> None:
    font = Font()
    for layer in (font.layers.defaultLayer, font.layers.newLayer("background")):
        layer.newGlyph("a").width = 100
        layer.newGlyph("composite").components.append(Component("a"))
    font.glyphOrder = ["a", "composite"]
    font.groups["example"] = ["a"]
    font.kerning[("a", "composite")] = 25
    font.renameGlyphs({"a": "new"})
    assert set(font.keys()) == {"new", "composite"}
    assert component_names(font.layers.defaultLayer, "composite") == ["new"]
    background = font.layers["background"]
    assert set(background.keys()) == {"a", "composite"}
    assert component_names(background, "composite") == ["a"]
    assert font.glyphOrder == ["a", "composite"]
    assert font.groups["example"] == ["a"]
    assert font.kerning[("a", "composite")] == 25
    background.renameGlyphs({"a": "background-a"})
    path = tmp_path / "layers.ufo"
    font.save(path)
    with Font.open(path) as reopened:
        assert component_names(reopened.layers.defaultLayer, "composite") == ["new"]
        assert component_names(reopened.layers["background"], "composite") == [
            "background-a"
        ]


def test_batch_lazy_roundtrip_and_validation_before_loading(tmp_path: Path) -> None:
    font = Font()
    layer = font.layers.defaultLayer
    for glyph in make_layer():
        layer.addGlyph(glyph)
    pen = font["a"].getPen()
    pen.moveTo((0, 0))
    pen.lineTo((20, 0))
    pen.lineTo((20, 30))
    pen.closePath()
    geometry = font["a"].contours.copy()
    source = tmp_path / "source.ufo"
    font.save(source)
    output = tmp_path / "renamed.ufo"
    with Font.open(source, lazy=True) as lazy:
        layer = lazy.layers.defaultLayer
        assert all(glyph is _GLYPH_NOT_LOADED for glyph in layer._glyphs.values())
        layer.renameGlyphs({})
        layer.renameGlyphs({"a": "a"})
        with pytest.raises(KeyError):
            layer.renameGlyphs({"a": "new", "b": "c"})
        assert all(glyph is _GLYPH_NOT_LOADED for glyph in layer._glyphs.values())
        with patch.object(
            Layer, "loadGlyph", autospec=True, side_effect=Layer.loadGlyph
        ) as load:
            layer.renameGlyphs({"a": "b", "b": "a", "composite": "combined"})
        assert load.call_count == len(layer)
        assert lazy["b"].contours == geometry
        assert component_names(layer, "combined") == ["b", "a", "b"]
        assert component_names(layer, "nested") == ["combined"]
        lazy.save(output)
    with Font.open(output) as reopened:
        assert reopened["b"].contours == geometry
        assert reopened["b"].width == 101
        assert component_names(reopened.layers.defaultLayer, "combined") == [
            "b",
            "a",
            "b",
        ]


def test_existing_single_rename_keeps_its_behavior() -> None:
    layer = make_layer()
    layer.renameGlyph("a", "new")
    assert "new" in layer
    assert component_names(layer, "composite") == ["a", "b", "a"]
