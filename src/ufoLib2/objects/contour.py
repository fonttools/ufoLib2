import attr
from typing import Optional

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

import warnings
from fontTools.pens.pointPen import PointToSegmentPen

from ufoLib2.objects.point import Point


@attr.s(slots=True)
class Contour(MutableSequence):
    points = attr.ib(default=attr.Factory(list), type=list)
    identifier = attr.ib(default=None, repr=False, type=Optional[str])

    # collections.abc.MutableSequence interface

    def __delitem__(self, index):
        del self.points[index]

    def __getitem__(self, index):
        return self.points[index]

    def __setitem__(self, index, point):
        if not isinstance(point, Point):
            raise TypeError("expected Point, found %s" % type(point).__name__)
        self.points[index] = point

    def __iter__(self):
        return iter(self.points)

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
        return self.points[0].type == "move"

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
                    segmentType=p.type,
                    smooth=p.smooth,
                    name=p.name,
                    identifier=p.identifier,
                )
        except TypeError:
            pointPen.beginPath()
            for p in self.points:
                pointPen.addPoint(
                    (p.x, p.y),
                    segmentType=p.type,
                    smooth=p.smooth,
                    name=p.name,
                )
            warnings.warn(
                "The pointPen needs an identifier kwarg. "
                "Identifiers have been discarded.",
                UserWarning,
            )
        pointPen.endPath()
