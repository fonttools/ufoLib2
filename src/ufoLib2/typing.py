import sys
from typing import TypeVar, Union

from fontTools.pens.basePen import AbstractPen
from fontTools.pens.pointPen import AbstractPointPen

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol


T = TypeVar("T")
"""Generic variable for mypy for trivial generic function signatures."""

Number = Union[int, float]
"""Used when integers and floats are interchangable according to the specification."""


class Drawable(Protocol):
    """Stand-in for an object that can draw itself with a given pen.

    See :mod:`fontTools.pens.basePen` and :mod:`fontTools.pens.pointPen` for an
    introduction to pens.
    """

    def draw(self, pen: AbstractPen) -> None:
        ...

    def drawPoints(self, pointPen: AbstractPointPen) -> None:
        ...
