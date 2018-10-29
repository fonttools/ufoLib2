import attr
from typing import Optional
from ufoLib2.objects.glyph import Glyph
from ufoLib2.objects.misc import _NOT_LOADED
from ufoLib2.constants import DEFAULT_LAYER_NAME


def _convert_glyphs(value):
    if isinstance(value, dict):
        return value
    result = {}
    for glyph in value:
        if glyph.name in result:
            raise KeyError("glyph %r already exists" % glyph.name)
        result[glyph.name] = glyph
    return result


@attr.s(slots=True, repr=False)
class Layer(object):
    _name = attr.ib(default=DEFAULT_LAYER_NAME, type=str)
    _glyphs = attr.ib(
        default=attr.Factory(dict), converter=_convert_glyphs, type=dict
    )
    color = attr.ib(default=None, type=Optional[str])
    lib = attr.ib(default=attr.Factory(dict), type=dict)

    _glyphSet = attr.ib(default=None, init=False)

    @classmethod
    def read(cls, name, glyphSet, lazy=True):
        glyphNames = glyphSet.keys()
        if lazy:
            glyphs = {gn: _NOT_LOADED for gn in glyphNames}
        else:
            glyphs = {}
            for glyphName in glyphNames:
                glyph = Glyph(glyphName)
                glyphSet.readGlyph(glyphName, glyph, glyph.getPointPen())
                glyphs[glyphName] = glyph
        self = cls(name, glyphs)
        if lazy:
            self._glyphSet = glyphSet
        glyphSet.readLayerInfo(self)
        return self

    def __contains__(self, name):
        return name in self._glyphs

    def __delitem__(self, name):
        del self._glyphs[name]

    def __getitem__(self, name):
        if self._glyphs[name] is _NOT_LOADED:
            return self.loadGlyph(name)
        return self._glyphs[name]

    def __setitem__(self, name, glyph):
        if not isinstance(glyph, Glyph):
            raise TypeError("Expected Glyph, found %s" % type(glyph).__name__)
        glyph._name = name
        self._glyphs[name] = glyph

    def __iter__(self):
        for name in self._glyphs:
            yield self[name]

    def __len__(self):
        return len(self._glyphs)

    def __repr__(self):
        n = len(self._glyphs)
        return "<{}.{} '{}' ({}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            self._name,
            "empty"
            if n == 0
            else "{} glyph{}".format(n, "s" if n > 1 else ""),
            hex(id(self)),
        )

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def keys(self):
        return self._glyphs.keys()

    def pop(self, name, default=KeyError):
        try:
            glyph = self[name]
        except KeyError:
            if default is KeyError:
                raise
            glyph = default
        else:
            del self[name]
        return glyph

    @property
    def name(self):
        return self._name

    def addGlyph(self, glyph):
        if glyph.name in self._glyphs:
            raise KeyError("glyph %r already exists" % glyph.name)
        self._glyphs[glyph.name] = glyph

    def loadGlyph(self, name):
        glyph = Glyph(name)
        self._glyphSet.readGlyph(name, glyph, glyph.getPointPen())
        self._glyphs[name] = glyph
        return glyph

    def newGlyph(self, name):
        if name in self._glyphs:
            raise KeyError("glyph %r already exists" % name)
        self._glyphs[name] = glyph = Glyph(name)
        return glyph

    def renameGlyph(self, name, newName, overwrite=False):
        if name == newName:
            return
        if not overwrite and newName in self._glyphs:
            raise KeyError("target glyph %r already exists" % newName)
        # pop and set name
        glyph = self.pop(name)
        glyph._name = newName
        # add it back
        self._glyphs[newName] = glyph

    def write(self, glyphSet, saveAs=True):
        glyphs = self._glyphs
        if not saveAs:
            for name in set(glyphSet.contents).difference(glyphs):
                glyphSet.deleteGlyph(name)
        for name, glyph in glyphs.items():
            if glyph is _NOT_LOADED:
                if saveAs:
                    glyph = self.loadGlyph(name)
                else:
                    continue
            glyphSet.writeGlyph(
                name, glyphObject=glyph, drawPointsFunc=glyph.drawPoints
            )
        glyphSet.writeContents()
        glyphSet.writeLayerInfo(self)
        if saveAs:
            # all glyphs are loaded by now, no need to keep ref to glyphSet
            self._glyphSet = None
