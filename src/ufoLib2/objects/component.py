import attr
from typing import Optional
from fontTools.misc.transform import Identity, Transform
from fontTools.pens.pointPen import PointToSegmentPen
import warnings


@attr.s(slots=True)
class Component(object):
    baseGlyph = attr.ib(type=str)
    transformation = attr.ib(
        default=Identity,
        convert=lambda t: t if isinstance(t, Transform) else Transform(*t),
        type=Transform,
    )
    identifier = attr.ib(default=None, type=Optional[str])

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
