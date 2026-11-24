from __future__ import annotations

import pytest

from ufoLib2.objects import Glyph, Point
from ufoLib2.objects.contour import Contour


@pytest.fixture
def contour() -> Contour:
    g = Glyph("a")
    pen = g.getPen()
    pen.moveTo((0, 0))
    pen.curveTo((10, 10), (10, 20), (0, 20))
    pen.closePath()
    return g.contours[0]


def test_contour_getBounds(contour: Contour) -> None:
    assert contour.getBounds() == (0, 0, 7.5, 20)
    assert contour.getBounds(layer={}) == (0, 0, 7.5, 20)
    assert contour.bounds == (0, 0, 7.5, 20)


def test_contour_getControlBounds(contour: Contour) -> None:
    assert contour.getControlBounds() == (0, 0, 10, 20)
    assert contour.getControlBounds(layer={}) == (0, 0, 10, 20)


@pytest.mark.parametrize("index", [slice(None), slice(1, 3), slice(None, None, 2)])
def test_contour_setitem_generator(index: slice) -> None:
    points = [Point(i, i) for i in range(4)]
    replacement = [Point(4, 4), Point(5, 5)]
    expected = points.copy()
    expected[index] = replacement
    contour = Contour(points)

    contour[index] = (point for point in replacement)

    assert list(contour) == expected


@pytest.mark.parametrize("index", [slice(None), slice(None, None, 2)])
def test_contour_setitem_invalid_generator(index: slice) -> None:
    points = [Point(i, i) for i in range(4)]
    contour = Contour(points.copy())
    replacement = (point for point in [Point(4, 4), object()])

    with pytest.raises(TypeError, match="Expected Point or Iterable"):
        contour[index] = replacement  # type: ignore

    assert list(contour) == points
