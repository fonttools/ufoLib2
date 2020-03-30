import warnings
from typing import Optional, Tuple

import attr
from fontTools.misc.transform import Identity, Transform
from fontTools.pens.pointPen import PointToSegmentPen

from ufoLib2.typing import Number

from .misc import _convert_transform, getBounds, getControlBounds


@attr.s(auto_attribs=True, slots=True)
class Component:
    baseGlyph: str
    transformation: Transform = attr.ib(default=Identity, converter=_convert_transform)
    identifier: Optional[str] = None

    def move(self, delta: Tuple[Number, Number]) -> None:
        x, y = delta
        self.transformation = self.transformation.translate(x, y)

    def getBounds(self, layer):
        return getBounds(self, layer)

    def getControlBounds(self, layer):
        return getControlBounds(self, layer)

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        try:
            pointPen.addComponent(
                self.baseGlyph, self.transformation, identifier=self.identifier
            )
        except TypeError:
            pointPen.addComponent(self.baseGlyph, self.transformation)
            warnings.warn(
                "The addComponent method needs an identifier kwarg. "
                "The component's identifier value has been discarded.",
                UserWarning,
            )
