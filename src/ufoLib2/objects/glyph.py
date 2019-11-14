from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

import attr
from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import PointToSegmentPen, SegmentToPointPen

from ufoLib2.objects.anchor import Anchor
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.image import Image
from ufoLib2.pointPens.glyphPointPen import GlyphPointPen


@attr.s(slots=True, repr=False)
class Glyph:
    _name = attr.ib(type=str)
    width = attr.ib(default=0, type=Union[int, float])
    height = attr.ib(default=0, type=Union[int, float])
    unicodes = attr.ib(default=attr.Factory(list), type=List[int])

    _image = attr.ib(default=attr.Factory(Image), type=Image)
    lib = attr.ib(default=attr.Factory(dict), type=Dict[str, Any])
    note = attr.ib(default=None, type=Optional[str])
    _anchors = attr.ib(default=attr.Factory(list), type=list)
    components = attr.ib(default=attr.Factory(list), type=list)
    contours = attr.ib(default=attr.Factory(list), type=list)
    _guidelines = attr.ib(default=attr.Factory(list), type=list)

    def __len__(self):
        return len(self.contours)

    def __getitem__(self, index):
        return self.contours[index]

    def __contains__(self, contour):
        return contour in self.contours

    def __iter__(self):
        return iter(self.contours)

    def __repr__(self):
        return "<{}.{} '{}' at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            self._name,
            hex(id(self)),
        )

    @property
    def anchors(self):
        return self._anchors

    @anchors.setter
    def anchors(self, value):
        self.clearAnchors()
        for anchor in value:
            self.appendAnchor(anchor)

    @property
    def guidelines(self):
        return self._guidelines

    @guidelines.setter
    def guidelines(self, value):
        self.clearGuidelines()
        for guideline in value:
            self.appendGuideline(guideline)

    @property
    def name(self):
        return self._name

    @property
    def unicode(self):
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
        del self._anchors[:]
        del self.components[:]
        del self.contours[:]
        del self._guidelines[:]
        self.image.clear()

    def clearAnchors(self):
        del self._anchors[:]

    def clearContours(self):
        del self.contours[:]

    def clearComponents(self):
        del self.components[:]

    def clearGuidelines(self):
        del self._guidelines[:]

    def removeComponent(self, component):
        self.components.remove(component)

    def appendAnchor(self, anchor):
        if not isinstance(anchor, Anchor):
            anchor = Anchor(**anchor)
        self.anchors.append(anchor)

    def appendGuideline(self, guideline):
        if not isinstance(guideline, Guideline):
            guideline = Guideline(**guideline)
        self._guidelines.append(guideline)

    def copy(self, name=None):
        """Return a new Glyph (deep) copy, optionally override the new glyph name.
        """
        other = deepcopy(self)
        if name is not None:
            other._name = name
        return other

    def copyDataFromGlyph(self, glyph):
        """Deep-copy everything from the other glyph, except for the name.
        Existing glyph data is overwritten.

        This method was added for compatibility with the defcon API, and
        it may be removed in the future.
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

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        for contour in self.contours:
            contour.drawPoints(pointPen)
        for component in self.components:
            component.drawPoints(pointPen)

    def getPen(self):
        pen = SegmentToPointPen(self.getPointPen())
        return pen

    def getPointPen(self):
        pointPen = GlyphPointPen(self)
        return pointPen

    # lib wrapped attributes

    @property
    def markColor(self):
        return self.lib.get("public.markColor")

    @markColor.setter
    def markColor(self, value):
        if value is not None:
            self.lib["public.markColor"] = value
        elif "public.markColor" in self.lib:
            del self.lib["public.markColor"]

    @property
    def verticalOrigin(self):
        return self.lib.get("public.verticalOrigin")

    @verticalOrigin.setter
    def verticalOrigin(self, value):
        if value is not None:
            self.lib["public.verticalOrigin"] = value
        elif "public.verticalOrigin" in self.lib:
            del self.lib["public.verticalOrigin"]
