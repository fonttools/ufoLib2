from __future__ import annotations

import pytest

from ufoLib2.objects import Component, Glyph, Layer


@pytest.fixture
def layer() -> Layer:
    a = Glyph("a")
    pen = a.getPen()
    pen.moveTo((0, 0))
    pen.curveTo((10, 10), (10, 20), (0, 20))
    pen.closePath()

    layer = Layer(glyphs=[a])
    return layer


def test_component_getBounds(layer: Layer) -> None:
    assert Component("a", (1, 0, 0, 1, 0, 0)).getBounds(layer) == (0, 0, 7.5, 20)
    assert Component("a", (1, 0, 0, 1, -5, 0)).getBounds(layer) == (-5, 0, 2.5, 20)
    assert Component("a", (1, 0, 0, 1, 0, 5)).getBounds(layer) == (0, 5, 7.5, 25)


def test_component_getControlBounds(layer: Layer) -> None:
    assert Component("a", (1, 0, 0, 1, 0, 0)).getControlBounds(layer) == (0, 0, 10, 20)
    assert Component("a", (1, 0, 0, 1, -5, 0)).getControlBounds(layer) == (-5, 0, 5, 20)
    assert Component("a", (1, 0, 0, 1, 0, 5)).getControlBounds(layer) == (0, 5, 10, 25)


def test_component_not_in_layer(layer: Layer) -> None:
    with pytest.raises(KeyError, match="b"):
        Component("b", (1, 0, 0, 1, 0, 0)).getBounds(layer)
    with pytest.raises(KeyError, match="b"):
        Component("b", (1, 0, 0, 1, 0, 0)).getControlBounds(layer)
