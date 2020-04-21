from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import attr
from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import PointToSegmentPen, SegmentToPointPen

from ufoLib2.objects.anchor import Anchor
from ufoLib2.objects.component import Component
from ufoLib2.objects.contour import Contour
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.image import Image
from ufoLib2.objects.misc import getBounds, getControlBounds
from ufoLib2.pointPens.glyphPointPen import GlyphPointPen
from ufoLib2.typing import Number


@attr.s(auto_attribs=True, slots=True, repr=False)
class Glyph:
    """Represents a glyph, containing contours, components, anchors and various
    other bits of data concerning it.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/.

    Behavior:
        The Glyph object has list-like behavior. This behavior allows you to interact
        with contour data directly. For example, to get a particular contour::

            contour = glyph[0]

        To iterate over all contours::

            for contour in glyph:
                ...

        To get the number of contours::

            contourCount = len(glyph)

        To check if a :class:`.Contour` object is in glyph::

            exists = contour in glyph

        To interact with components or anchors in a similar way, use the
        :attr:`.Glyph.components` and :attr:`.Glyph.anchors` attributes.
    """

    _name: Optional[str] = None

    width: Number = 0
    """The width of the glyph."""

    height: Number = 0
    """The height of the glyph."""

    unicodes: List[int] = attr.ib(factory=list)
    """The Unicode code points assigned to the glyph. Note that a glyph can have
    multiple."""

    _image: Image = attr.ib(factory=Image)

    lib: Dict[str, Any] = attr.ib(factory=dict)
    """The glyph's mapping of string keys to arbitrary data."""

    note: Optional[str] = None
    """A free form text note about the glyph."""

    _anchors: List[Anchor] = attr.ib(factory=list)
    components: List[Component] = attr.ib(factory=list)
    """The list of components the glyph contains."""

    contours: List[Contour] = attr.ib(factory=list)
    """The list of contours the glyph contains."""

    _guidelines: List[Guideline] = attr.ib(factory=list)

    def __len__(self):
        return len(self.contours)

    def __getitem__(self, index):
        return self.contours[index]

    def __contains__(self, contour):
        return contour in self.contours

    def __iter__(self):
        return iter(self.contours)

    def __repr__(self):
        return "<{}.{} {}at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            f"'{self._name}' " if self._name is not None else "",
            hex(id(self)),
        )

    @property
    def anchors(self):
        """The list of anchors the glyph contains.

        Getter:
            Returns a list of anchors the glyph contains. Modifications of the list
            modify the Glyph object.

        Setter:
            Clears current anchors and sets the new ones.
        """
        return self._anchors

    @anchors.setter
    def anchors(self, value):
        self.clearAnchors()
        for anchor in value:
            self.appendAnchor(anchor)

    @property
    def guidelines(self):
        """The list of guidelines the glyph contains.

        Getter:
            Returns a list of guidelines the glyph contains. Modifications of the list
            modify the Glyph object.

        Setter:
            Clears current guidelines and sets the new ones.
        """
        return self._guidelines

    @guidelines.setter
    def guidelines(self, value):
        self.clearGuidelines()
        for guideline in value:
            self.appendGuideline(guideline)

    @property
    def name(self):
        """The name of the glyph."""
        return self._name

    @property
    def unicode(self):
        """The first assigned Unicode code point or None.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#unicode.

        Setter:
            Sets the value to be the first of the assigned Unicode code points. Will
            remove a duplicate if exists. Will clear the list of Unicode points if
            value is None.
        """
        if self.unicodes:
            return self.unicodes[0]
        return None

    @unicode.setter
    def unicode(self, value):
        if value is None:
            self.unicodes = []
        else:
            if self.unicodes:
                if self.unicodes[0] == value:
                    return
                try:
                    self.unicodes.remove(value)
                except ValueError:
                    pass
                self.unicodes.insert(0, value)
            else:
                self.unicodes.append(value)

    @property
    def image(self):
        """The background image reference associated with the glyph.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#image.

        Setter:
            Sets the background image reference. Clears it if value is None.
        """
        return self._image

    @image.setter
    def image(self, image):
        if image is None:
            self._image.clear()
        elif isinstance(image, Image):
            self._image = image
        else:
            self._image = Image(
                fileName=image["fileName"],
                transformation=Transform(
                    image["xScale"],
                    image["xyScale"],
                    image["yxScale"],
                    image["yScale"],
                    image["xOffset"],
                    image["yOffset"],
                ),
                color=image.get("color"),
            )

    def clear(self):
        """Clears out anchors, components, contours, guidelines and image
        references."""
        del self._anchors[:]
        del self.components[:]
        del self.contours[:]
        del self._guidelines[:]
        self.image.clear()

    def clearAnchors(self):
        """Clears out anchors."""
        del self._anchors[:]

    def clearContours(self):
        """Clears out contours."""
        del self.contours[:]

    def clearComponents(self):
        """Clears out components."""
        del self.components[:]

    def clearGuidelines(self):
        """Clears out guidelines."""
        del self._guidelines[:]

    def removeComponent(self, component):
        """Removes :class:`.Component` object from the glyph's list of components."""
        self.components.remove(component)

    def appendAnchor(self, anchor):
        """Appends :class:`.Anchor` object to glyph's list of anchors."""
        if not isinstance(anchor, Anchor):
            anchor = Anchor(**anchor)
        self.anchors.append(anchor)

    def appendGuideline(self, guideline):
        """Appends :class:`.Guideline` object to glyph's list of guidelines."""
        if not isinstance(guideline, Guideline):
            guideline = Guideline(**guideline)
        self._guidelines.append(guideline)

    def appendContour(self, contour):
        """Appends :class:`.Contour` object to glyph's list of contours."""
        if not isinstance(contour, Contour):
            raise TypeError(
                f"Expected {Contour.__name__}, found {type(contour).__name__}"
            )
        self.contours.append(contour)

    def copy(self, name=None):
        """Returns a new Glyph (deep) copy, optionally override the new glyph
        name."""
        other = deepcopy(self)
        if name is not None:
            other._name = name
        return other

    def copyDataFromGlyph(self, glyph):
        """Deep-copies everything from the other glyph into self, except for
        the name.

        Existing glyph data is overwritten.

        |defcon_compat|
        """
        self.width = glyph.width
        self.height = glyph.height
        self.unicodes = list(glyph.unicodes)
        self.image = deepcopy(glyph.image)
        self.note = glyph.note
        self.lib = deepcopy(glyph.lib)
        self.anchors = deepcopy(glyph.anchors)
        self.guidelines = deepcopy(glyph.guidelines)
        # NOTE: defcon's copyDataFromGlyph appends instead of overwrites here,
        # but we do the right thing, for consistency with the rest.
        self.clearContours()
        self.clearComponents()
        pointPen = self.getPointPen()
        glyph.drawPoints(pointPen)

    def move(self, delta: Tuple[Number, Number]) -> None:
        """Moves all contours, components and anchors by (x, y) font units."""
        for contour in self.contours:
            contour.move(delta)
        for component in self.components:
            component.move(delta)
        for anchor in self.anchors:
            anchor.move(delta)

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        """Draws glyph into given pen."""
        # TODO: Document pen interface more or link to somewhere.
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """Draws points of glyph into given point pen."""
        for contour in self.contours:
            contour.drawPoints(pointPen)
        for component in self.components:
            component.drawPoints(pointPen)

    def getPen(self):
        """Returns a pen for others to draw into self."""
        pen = SegmentToPointPen(self.getPointPen())
        return pen

    def getPointPen(self):
        """Returns a point pen for others to draw points into self."""
        pointPen = GlyphPointPen(self)
        return pointPen

    # lib wrapped attributes

    @property
    def markColor(self):
        """The color assigned to the glyph.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#publicmarkcolor.

        Getter:
            Returns the mark color or None.

        Setter:
            Sets the mark color. If value is None, deletes the key from the lib if
            present.
        """
        return self.lib.get("public.markColor")

    @markColor.setter
    def markColor(self, value):
        if value is not None:
            self.lib["public.markColor"] = value
        elif "public.markColor" in self.lib:
            del self.lib["public.markColor"]

    @property
    def verticalOrigin(self):
        """The vertical origin of the glyph.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#publicverticalorigin.

        Getter:
            Returns the vertical origin or None.

        Setter:
            Sets the vertical origin. If value is None, deletes the key from the lib if
            present.
        """
        return self.lib.get("public.verticalOrigin")

    @verticalOrigin.setter
    def verticalOrigin(self, value):
        if value is not None:
            self.lib["public.verticalOrigin"] = value
        elif "public.verticalOrigin" in self.lib:
            del self.lib["public.verticalOrigin"]

    # bounds and side-bearings

    def getBounds(self, layer=None):
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the glyph,
        taking the actual contours into account.

        Args:
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        if layer is None and self.components:
            raise TypeError("layer is required to compute bounds of components")

        return getBounds(self, layer)

    def getControlBounds(self, layer=None):
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the glyph,
        taking only the control points into account.

        Gives inaccurate results with extruding curvatures.

        Args:
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        if layer is None and self.components:
            raise TypeError("layer is required to compute bounds of components")

        return getControlBounds(self, layer)

    def getLeftMargin(self, layer=None):
        """Returns the the space in font units from the point of origin to the
        left side of the glyph.

        Args:
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        return bounds.xMin

    def setLeftMargin(self, value, layer=None):
        """Sets the the space in font units from the point of origin to the
        left side of the glyph.

        Args:
            value: The desired left margin in font units.
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        diff = value - bounds.xMin
        if diff:
            self.width += diff
            self.move((diff, 0))

    def getRightMargin(self, layer=None):
        """Returns the the space in font units from the glyph's advance width
        to the right side of the glyph.

        Args:
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        return self.width - bounds.xMax

    def setRightMargin(self, value, layer=None):
        """Sets the the space in font units from the glyph's advance width to
        the right side of the glyph.

        Args:
            value: The desired right margin in font units.
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        self.width = bounds.xMax + value

    def getBottomMargin(self, layer=None):
        """Returns the the space in font units from the bottom of the canvas to
        the bottom of the glyph.

        Args:
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        if self.verticalOrigin is None:
            return bounds.yMin
        else:
            return bounds.yMin - (self.verticalOrigin - self.height)

    def setBottomMargin(self, value, layer=None):
        """Sets the the space in font units from the bottom of the canvas to
        the bottom of the glyph.

        Args:
            value: The desired bottom margin in font units.
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        # blindly copied from defcon Glyph._set_bottomMargin; not sure it's correct
        if self.verticalOrigin is None:
            oldValue = bounds.yMin
            self.verticalOrigin = self.height
        else:
            oldValue = bounds.yMin - (self.verticalOrigin - self.height)
        diff = value - oldValue
        if diff:
            self.height += diff

    def getTopMargin(self, layer=None):
        """Returns the the space in font units from the top of the canvas to
        the top of the glyph.

        Args:
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return None
        if self.verticalOrigin is None:
            return self.height - bounds.yMax
        else:
            return self.verticalOrigin - bounds.yMax

    def setTopMargin(self, value, layer=None):
        """Sets the the space in font units from the top of the canvas to the
        top of the glyph.

        Args:
            value: The desired top margin in font units.
            layer: The layer of the glyph to look up components, if any. Not needed for
                pure-contour glyphs.
        """
        bounds = self.getBounds(layer)
        if bounds is None:
            return
        if self.verticalOrigin is None:
            oldValue = self.height - bounds.yMax
        else:
            oldValue = self.verticalOrigin - bounds.yMax
        diff = value - oldValue
        if oldValue != value:
            # Is this still correct when verticalOrigin was not previously set?
            self.verticalOrigin = bounds.yMax + value
            self.height += diff
