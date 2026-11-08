from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from ufoLib2 import Font
from ufoLib2.objects import Glyph, Layer, LayerSet
from ufoLib2.objects.layer import _GLYPH_NOT_LOADED
from ufoLib2.objects.layerSet import _LAYER_NOT_LOADED


@pytest.mark.parametrize("kind", ["font", "layer"])
def test_empty_glyph_items(kind: str) -> None:
    font = Font()
    container = font if kind == "font" else font.layers.defaultLayer
    items = container.items()
    assert isinstance(items, Iterator)
    assert list(items) == []


@pytest.mark.parametrize("kind", ["font", "layer"])
def test_glyph_items_keys_objects_and_iteration(kind: str) -> None:
    font = Font()
    a = font.newGlyph("A")
    b = font.newGlyph("B")
    container = font if kind == "font" else font.layers.defaultLayer
    pairs = list(container.items())
    assert [name for name, glyph in pairs] == list(container.keys()) == ["A", "B"]
    assert pairs[0][1] is a
    assert pairs[1][1] is b
    assert all(
        isinstance(name, str) and isinstance(glyph, Glyph) for name, glyph in pairs
    )
    assert list(container) == [a, b]


def test_default_layer_items() -> None:
    layers = LayerSet.default()
    pairs = list(layers.items())
    assert len(pairs) == 1
    assert pairs[0][0] == "public.default"
    assert pairs[0][1] is layers.defaultLayer


def test_layer_items_keys_objects_and_iteration() -> None:
    layers = LayerSet.default()
    background = layers.newLayer("background")
    foreground = layers.newLayer("foreground")
    pairs = list(layers.items())
    assert [name for name, layer in pairs] == list(layers.keys())
    assert [layer for name, layer in pairs] == list(layers)
    assert pairs[1][1] is background
    assert pairs[2][1] is foreground
    assert all(
        isinstance(name, str) and isinstance(layer, Layer) for name, layer in pairs
    )


def make_synthetic_font(path: Path) -> None:
    font = Font()
    for name in ["A", "B", "C"]:
        font.newGlyph(name)
    for name in ["background", "foreground"]:
        layer = font.layers.newLayer(name)
        layer.newGlyph("A")
    font.save(path)
    font.close()


@pytest.mark.parametrize("kind", ["font", "layer"])
def test_glyph_items_load_only_as_consumed(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "synthetic.ufo"
    make_synthetic_font(path)
    with Font.open(path, lazy=True) as font:
        layer = font.layers.defaultLayer
        container = font if kind == "font" else layer
        names = list(container.keys())
        assert len(names) == 3
        assert all(value is _GLYPH_NOT_LOADED for value in layer._glyphs.values())
        items = container.items()
        assert iter(items) is items
        assert all(value is _GLYPH_NOT_LOADED for value in layer._glyphs.values())

        name, glyph = next(items)
        assert name == names[0]
        assert glyph is layer[name]
        assert all(layer._glyphs[n] is _GLYPH_NOT_LOADED for n in names[1:])

        remaining = list(items)
        assert [name for name, glyph in remaining] == names[1:]
        assert all(glyph is layer[name] for name, glyph in remaining)
        assert all(value is not _GLYPH_NOT_LOADED for value in layer._glyphs.values())


def test_layers_items_load_only_as_consumed(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.ufo"
    make_synthetic_font(path)
    with Font.open(path, lazy=True) as font:
        layers = font.layers
        names = list(layers.keys())
        before = dict(layers._layers)
        items = layers.items()
        assert iter(items) is items
        assert all(layers._layers[name] is value for name, value in before.items())

        name, layer = next(items)
        assert name == names[0]
        assert layer is layers[name]
        assert all(layers._layers[n] is before[n] for n in names[1:])

        name, layer = next(items)
        assert name == names[1]
        assert layer is layers[name]
        assert layers._layers[names[2]] is _LAYER_NOT_LOADED
        assert all(value is _GLYPH_NOT_LOADED for value in layer._glyphs.values())

        last_name, last_layer = next(items)
        assert last_name == names[2]
        assert last_layer is layers[last_name]
        with pytest.raises(StopIteration):
            next(items)
