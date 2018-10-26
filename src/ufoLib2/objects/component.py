from fontTools.misc.transform import Identity, Transform
from fontTools.pens.pointPen import PointToSegmentPen
import warnings
from ufoLib2.objects.misc import AttrReprMixin


class Component(AttrReprMixin):
    __slots__ = _fields = ("baseGlyph", "transformation", "identifier")

    def __init__(self, baseGlyph, transformation=Identity, identifier=None):
        self.baseGlyph = baseGlyph
        if isinstance(transformation, Transform):
            self.transformation = transformation
        else:
            self.transformation = Transform(*transformation)
        self.identifier = identifier

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
