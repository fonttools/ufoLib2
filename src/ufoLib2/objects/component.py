import attr
from typing import Optional
from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import PointToSegmentPen
import warnings


@attr.s(slots=True)
class Component(object):
    baseGlyph = attr.ib(type=str)
    _transformation = attr.ib(
        convert=lambda t: t if isinstance(t, Transform) else Transform(*t),
        type=Transform,
    )
    identifier = attr.ib(default=None, type=Optional[str])

    @property
    def transformation(self):
        return self._transformation

    @transformation.setter
    def transformation(self, value):
        self._transformation = (
            value if isinstance(value, Transform) else Transform(*value)
        )

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        try:
            pointPen.addComponent(
                self.baseGlyph,
                self._transformation,
                identifier=self.identifier,
            )
        except TypeError:
            pointPen.addComponent(self.baseGlyph, self._transformation)
            warnings.warn(
                "The addComponent method needs an identifier kwarg. "
                "The component's identifier value has been discarded.",
                UserWarning,
            )
