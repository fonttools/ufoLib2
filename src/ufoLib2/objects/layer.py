from typing import Any, Dict, Optional, Sequence, Union

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


@attr.s(auto_attribs=True, slots=True, repr=False)
class Layer:
    """Represents a Layer that holds Glyph objects.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/layerinfo.plist/.

    Note:
        Various methods that work on Glyph objects take a ``layer`` attribute, because
        the UFO data model prescribes that Components within a Glyph object refer to
        glyphs *within the same layer*.

    Behavior:
        Layer behaves **partly** like a dictionary of type ``Dict[str, Glyph]``.
        Unless the font is loaded eagerly (with ``lazy=False``), the Glyph objects
        by default are only loaded into memory when accessed.

        To get the number of glyphs in the layer::

            glyphCount = len(layer)

        To iterate over all glyphs::

            for glyph in layer:
                ...

        To check if a specific glyph exists::

            exists = "myGlyphName" in layer

        To get a specific glyph::

            layer["myGlyphName"]

        To delete a specific glyph::

            del layer["myGlyphName"]
    """

    _name: str = DEFAULT_LAYER_NAME
    _glyphs: Dict[str, Glyph] = attr.ib(factory=dict, converter=_convert_glyphs)
    color: Optional[str] = None
    """The color assigned to the layer."""

    lib: Dict[str, Any] = attr.ib(factory=dict)
    """The layer's lib for mapping string keys to arbitrary data."""

    _glyphSet: Any = attr.ib(default=None, init=False, eq=False)

    @classmethod
    def read(cls, name, glyphSet, lazy=True):
        """Instantiates a Layer object from a
        :class:`fontTools.ufoLib.glifLib.GlyphSet`.

        Args:
            name: The name of the layer.
            glyphSet: The GlyphSet object to read from.
            lazy: If True, load glyphs as they are accessed. If False, load everything
                up front.
        """
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
        """Load all glyphs into memory."""
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
        """Return the Glyph object for name if it is present in this layer,
        otherwise return ``default``."""
        try:
            return self[name]
        except KeyError:
            return default

    def keys(self):
        """Returns a list of glyph names."""
        return self._glyphs.keys()

    def pop(self, name, default=KeyError):
        """Remove and return glyph from layer.

        Args:
            name: The name of the glyph.
            default: What to return if there is no glyph with the given name.
        """
        # XXX: make `default` a None instead of KeyError?
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
        """The name of the layer."""
        return self._name

    def addGlyph(self, glyph):
        """Appends glyph object to the this layer unless its name is already
        taken."""
        self.insertGlyph(glyph, overwrite=False, copy=False)

    def insertGlyph(self, glyph, name=None, overwrite=True, copy=True):
        """Inserts Glyph object into this layer.

        Args:
            glyph: The Glyph object.
            name: The name of the glyph.
            overwrite: If True, overwrites (read: deletes) glyph with the same name if
                it exists. If False, raises KeyError.
            copy: If True, copies the Glyph object before insertion. If False, inserts
                as is.
        """
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
        """Load and return Glyph object."""
        # XXX: Remove and let __getitem__ do it?
        glyph = Glyph(name)
        self._glyphSet.readGlyph(name, glyph, glyph.getPointPen())
        self._glyphs[name] = glyph
        return glyph

    def newGlyph(self, name):
        """Creates and returns new Glyph object in this layer with name."""
        if name in self._glyphs:
            raise KeyError(f"glyph named '{name}' already exists")
        self._glyphs[name] = glyph = Glyph(name)
        return glyph

    def renameGlyph(self, name, newName, overwrite=False):
        """Renames a Glyph object in this layer.

        Args:
            name: The old name.
            newName: The new name.
            overwrite: If False, raises exception if newName is already taken.
                If True, overwrites (read: deletes) the old Glyph object.
        """
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
        """Returns a new Glyph instance.

        |defcon_compat|
        """
        return Glyph()

    def write(self, glyphSet, saveAs=True):
        """Write Layer to a :class:`fontTools.ufoLib.glifLib.GlyphSet`.

        Args:
            glyphSet: The GlyphSet object to write to.
            saveAs: If True, tells the writer to save out-of-place. If False, tells the
                writer to save in-place. This affects how resources are cleaned before
                writing.
        """
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
