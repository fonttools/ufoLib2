import warnings
from collections.abc import MutableSequence
from typing import List, Optional, Tuple

import attr
from fontTools.pens.pointPen import PointToSegmentPen

from ufoLib2.objects.misc import getBounds, getControlBounds
from ufoLib2.objects.point import Point
from ufoLib2.typing import Number


@attr.s(auto_attribs=True, slots=True)
class Contour(MutableSequence):
    """Represents a contour as a list of points.

    Behavior:
        The Contour object has list-like behavior. This behavior allows you to interact
        with point data directly. For example, to get a particular point::

            point = contour[0]

        To iterate over all points::

            for point in contour:
                ...

        To get the number of points::

            pointCount = len(contour)

        To delete a particular point::

            del contour[0]

        To set a particular point to another Point object::

            contour[0] = anotherPoint
    """

    points: List[Point] = attr.ib(factory=list)
    """The list of points in the contour."""

    identifier: Optional[str] = attr.ib(default=None, repr=False)
    """The globally unique identifier of the contour."""

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
        """Insert Point object ``point`` into the contour at ``index``."""
        if not isinstance(point, Point):
            raise TypeError("expected Point, found %s" % type(point).__name__)
        self.points.insert(index, point)

    # TODO: rotate method?

    @property
    def open(self):
        """Returns whether the contour is open or closed."""
        if not self.points:
            return True
        return self.points[0].type == "move"

    def move(self, delta: Tuple[Number, Number]) -> None:
        """Moves contour by (x, y) font units."""
        for point in self.points:
            point.move(delta)

    def getBounds(self, layer=None):
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the glyph,
        taking the actual contours into account.

        Args:
            layer: Not applicable to contours, here for API symmetry.
        """
        return getBounds(self, layer)

    @property
    def bounds(self):
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the glyph,
        taking the actual contours into account.

        |defcon_compat|
        """
        return self.getBounds()

    def getControlBounds(self, layer=None):
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the glyph,
        taking only the control points into account.

        Gives inaccurate results with extruding curvatures.

        Args:
            layer: Not applicable to contours, here for API symmetry.
        """
        return getControlBounds(self, layer)

    # XXX: Add property controlPointBounds (defcon compat API)?

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        """Draws contour into given pen."""
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """Draws points of contour into given point pen."""
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
                    (p.x, p.y), segmentType=p.type, smooth=p.smooth, name=p.name
                )
            warnings.warn(
                "The pointPen needs an identifier kwarg. "
                "Identifiers have been discarded.",
                UserWarning,
            )
        pointPen.endPath()
