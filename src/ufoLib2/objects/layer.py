import attr
from typing import Optional
from ufoLib2.objects.glyph import Glyph
from ufoLib2.objects.misc import _NOT_LOADED
from ufoLib2.constants import DEFAULT_LAYER_NAME


@attr.s(slots=True)
class Layer(object):
    _name = attr.ib(default=DEFAULT_LAYER_NAME, type=str)
    _glyphs = attr.ib(default=attr.Factory(dict), repr=False, type=dict)
    color = attr.ib(default=None, repr=False, type=Optional[str])
    lib = attr.ib(default=attr.Factory(dict), repr=False, type=dict)

    _glyphSet = attr.ib(default=None, repr=False)
    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, repr=False
    )

    @classmethod
    def read(cls, name, glyphSet, lazy=True):
        self = cls(name, glyphSet=glyphSet)
        glyphNames = glyphSet.keys()
        if lazy:
            self._glyphs = {name: _NOT_LOADED for name in glyphNames}
        else:
            try:
                for name in glyphNames:
                    self.loadGlyph(name)
            finally:
                # all glyphs loaded, we're done with the glyphSet
                self._glyphSet = None
        glyphSet.readLayerInfo(self)
        return self

    def __contains__(self, name):
        return name in self._glyphs

    def __delitem__(self, name):
        if name not in self._glyphs:
            raise KeyError("name %r is not in layer" % name)
        self._delete(name)

    def __getitem__(self, name):
        if self._glyphs[name] is _NOT_LOADED:
            self.loadGlyph(name)
        return self._glyphs[name]

    def __iter__(self):
        for name in self._glyphs:
            yield self[name]

    def __len__(self):
        return len(self._glyphs)

    def _delete(self, name):
        # if the glyph is loaded, delete it
        if name in self._glyphs:
            del self._glyphs[name]
        # if the glyph is on disk, schedule for removal
        if self._glyphSet is not None and name in self._glyphSet:
            self._scheduledForDeletion.add(name)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def keys(self):
        return self._glyphs.keys()

    @property
    def name(self):
        return self._name

    def addGlyph(self, glyph):
        if glyph.name in self._glyphs:
            raise KeyError("glyph %r already exists" % glyph.name)
        self._glyphs[glyph.name] = glyph
        if glyph.name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(glyph.name)

    def loadGlyph(self, name):
        if (
            self._glyphSet is None
            or name not in self._glyphSet
            or name in self._scheduledForDeletion
        ):
            raise KeyError("name %r not in layer" % name)
        glyph = Glyph(name)
        self._glyphSet.readGlyph(name, glyph, glyph.getPointPen())
        self._glyphs[name] = glyph

    def newGlyph(self, name):
        if name in self._glyphs:
            raise KeyError("glyph %r already exists" % name)
        self._glyphs[name] = glyph = Glyph(name)
        if name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(name)
        return glyph

    def renameGlyph(self, name, newName, overwrite=False):
        if name == newName:
            return
        if not overwrite and newName in self._glyphs:
            raise KeyError("target glyph %r already exists" % newName)
        # load-get and delete
        glyph = self[name]
        self._delete(name)
        # add new
        self._glyphs[newName] = glyph
        if newName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(newName)
        # set name
        glyph._name = newName

    def write(self, glyphSet, saveAs=False):
        if saveAs:
            glyphs = self
        else:
            glyphs = self._glyphs.values()
            for name in self._scheduledForDeletion:
                if name in glyphSet:
                    glyphSet.deleteGlyph(name)
        for glyph in glyphs:
            glyphSet.writeGlyph(
                glyph.name, glyphObject=glyph, drawPointsFunc=glyph.drawPoints
            )
        glyphSet.writeContents()
        glyphSet.writeLayerInfo(self)
        if saveAs:
            # all glyphs are loaded by now, no need to keep ref to glyphSet
            self._glyphSet = None
        self._scheduledForDeletion = set()
