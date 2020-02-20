from typing import Dict, Optional, Sequence, Union

import attr

from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.objects.glyph import Glyph
from ufoLib2.objects.misc import _NOT_LOADED, _deepcopy_unlazify_attrs


def _convert_glyphs(
    value: Union[Dict[str, Glyph], Sequence[Glyph]]
) -> Dict[str, Glyph]:
    result: Dict[str, Glyph] = {}
    glyph_ids = set()
    if isinstance(value, dict):
        for name, glyph in value.items():
            if glyph is not _NOT_LOADED:
                if not isinstance(glyph, Glyph):
                    raise TypeError(f"Expected Glyph, found {type(glyph).__name__}")
                glyph_id = id(glyph)
                if glyph_id in glyph_ids:
                    raise KeyError(f"{glyph!r} can't be added twice")
                glyph_ids.add(glyph_id)
                if glyph.name is None:
                    glyph._name = name
                elif glyph.name != name:
                    raise ValueError(
                        "glyph has incorrect name: "
                        f"expected '{name}', found '{glyph.name}'"
                    )
            result[name] = glyph
    else:
        for glyph in value:
            if not isinstance(glyph, Glyph):
                raise TypeError(f"Expected Glyph, found {type(glyph).__name__}")
            glyph_id = id(glyph)
            if glyph_id in glyph_ids:
                raise KeyError(f"{glyph!r} can't be added twice")
            glyph_ids.add(glyph_id)
            if glyph.name is None:
                raise ValueError(f"{glyph!r} has no name; can't add it to Layer")
            if glyph.name in result:
                raise KeyError(f"glyph named '{glyph.name}' already exists")
            result[glyph.name] = glyph
    return result


@attr.s(slots=True, repr=False)
class Layer:
    _name = attr.ib(default=DEFAULT_LAYER_NAME, type=str)
    _glyphs = attr.ib(default=attr.Factory(dict), converter=_convert_glyphs, type=dict)
    color = attr.ib(default=None, type=Optional[str])
    lib = attr.ib(default=attr.Factory(dict), type=dict)

    _glyphSet = attr.ib(default=None, init=False, eq=False)

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

    def unlazify(self):
        for _ in self:
            pass

    __deepcopy__ = _deepcopy_unlazify_attrs

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
            raise TypeError(f"Expected Glyph, found {type(glyph).__name__}")
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
            "empty" if n == 0 else "{} glyph{}".format(n, "s" if n > 1 else ""),
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
        self.insertGlyph(glyph, overwrite=False, copy=False)

    def insertGlyph(self, glyph, name=None, overwrite=True, copy=True):
        if copy:
            glyph = glyph.copy()
        if name is not None:
            glyph._name = name
        if glyph.name is None:
            raise ValueError(f"{glyph!r} has no name; can't add it to Layer")
        if not overwrite and glyph.name in self._glyphs:
            raise KeyError(f"glyph named '{glyph.name}' already exists")
        self._glyphs[glyph.name] = glyph

    def loadGlyph(self, name):
        glyph = Glyph(name)
        self._glyphSet.readGlyph(name, glyph, glyph.getPointPen())
        self._glyphs[name] = glyph
        return glyph

    def newGlyph(self, name):
        if name in self._glyphs:
            raise KeyError(f"glyph named '{name}' already exists")
        self._glyphs[name] = glyph = Glyph(name)
        return glyph

    def renameGlyph(self, name, newName, overwrite=False):
        if name == newName:
            return
        if not overwrite and newName in self._glyphs:
            raise KeyError(f"target glyph named '{newName}' already exists")
        # pop and set name
        glyph = self.pop(name)
        glyph._name = newName
        # add it back
        self._glyphs[newName] = glyph

    def instantiateGlyphObject(self):
        # only for defcon API compatibility
        return Glyph()

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
