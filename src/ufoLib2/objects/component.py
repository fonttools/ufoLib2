import warnings
from typing import Optional

import attr
from fontTools.misc.transform import Identity, Transform
from fontTools.pens.pointPen import PointToSegmentPen

from .misc import _convert_transform


@attr.s(slots=True)
class Component:
    baseGlyph = attr.ib(type=str)
    transformation = attr.ib(
        default=Identity, converter=_convert_transform, type=Transform
    )
    identifier = attr.ib(default=None, type=Optional[str])

    def move(self, delta):
        x, y = delta
        self.transformation = self.transformation.translate(x, y)

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
