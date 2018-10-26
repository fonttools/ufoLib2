from fontTools.pens.pointPen import PointToSegmentPen
import warnings

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence
from ufoLib2.objects.misc import AttrReprMixin
from ufoLib2.objects.point import Point


class Contour(AttrReprMixin, MutableSequence):
    __slots__ = _fields = ("points", "identifier")

    def __init__(self, points=None, identifier=None):
        self.points = [] if points is None else points
        self.identifier = identifier

    # collections.abc.MutableSequence interface

    def __delitem__(self, index):
        del self.points[index]

    def __getitem__(self, index):
        return self.points[index]

    def __setitem__(self, index, point):
        if not isinstance(point, Point):
            raise TypeError("expected Point, found %s" % type(point).__name__)
        self.points[index] = point

    def __len__(self):
        return len(self.points)

    def insert(self, index, point):
        if not isinstance(point, Point):
            raise TypeError("expected Point, found %s" % type(point).__name__)
        self.points.insert(index, point)

    # TODO: rotate method?

    @property
    def open(self):
        if not self.points:
            return True
        return self.points[0].segmentType == "move"

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        try:
            pointPen.beginPath(identifier=self.identifier)
            for p in self.points:
                pointPen.addPoint(
                    (p.x, p.y),
                    segmentType=p.segmentType,
                    smooth=p.smooth,
                    name=p.name,
                    identifier=p.identifier,
                )
        except TypeError:
            pointPen.beginPath()
            for p in self.points:
                pointPen.addPoint(
                    (p.x, p.y),
                    segmentType=p.segmentType,
                    smooth=p.smooth,
                    name=p.name,
                )
            warnings.warn(
                "The pointPen needs an identifier kwarg. "
                "Identifiers have been discarded.",
                UserWarning,
            )
        pointPen.endPath()
