from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    KeysView,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    overload,
)

import attr
import readwrite_ufo_glif
from fontTools.ufoLib.glifLib import GlyphSet

from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.objects.anchor import Anchor
from ufoLib2.objects.component import Component
from ufoLib2.objects.contour import Contour
from ufoLib2.objects.glyph import Glyph
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.image import Image
from ufoLib2.objects.misc import (
    _NOT_LOADED,
    BoundingBox,
    Placeholder,
    _deepcopy_unlazify_attrs,
    _prune_object_libs,
    unionBounds,
)
from ufoLib2.objects.point import Point
from ufoLib2.typing import T


def _convert_glyphs(
    value: Union[Dict[str, Union[Glyph, Placeholder]], Sequence[Glyph]]
) -> Dict[str, Union[Glyph, Placeholder]]:
    result: Dict[str, Union[Glyph, Placeholder]] = {}
    glyph_ids = set()
    if isinstance(value, dict):
        for name, glyph in value.items():
            if not isinstance(glyph, Placeholder):
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
class MinimalGlyphSet:
    path: Path
    contents: Dict[str, str]

    @classmethod
    def from_path(cls, path: Path) -> "MinimalGlyphSet":
        return cls(path, readwrite_ufo_glif.read_layer_contents(str(path)))


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
    _glyphs: Dict[str, Union[Glyph, Placeholder]] = attr.ib(
        factory=dict, converter=_convert_glyphs
    )
    color: Optional[str] = None
    """The color assigned to the layer."""

    lib: Dict[str, Any] = attr.ib(factory=dict)
    """The layer's lib for mapping string keys to arbitrary data."""

    _glyphSet: Any = attr.ib(default=None, init=False, eq=False)

    @classmethod
    def read(cls, name: str, path: Path, lazy: bool = True) -> "Layer":
        """Instantiates a Layer object from a
        :class:`fontTools.ufoLib.glifLib.GlyphSet`.

        Args:
            name: The name of the layer.
            glyphSet: The GlyphSet object to read from.
            lazy: If True, load glyphs as they are accessed. If False, load everything
                up front.
        """

        glyphs: Dict[str, Union[Glyph, Placeholder]]
        if lazy:
            glyphset = MinimalGlyphSet.from_path(path)
            glyphs = {gn: _NOT_LOADED for gn in glyphset.contents.keys()}
            color, lib = readwrite_ufo_glif.read_layerinfo_maybe(str(path))
            self = cls(name, glyphs, color=color, lib=lib)
            self._glyphSet = glyphset
        else:
            glyphs, layerinfo = _read_layer(path)
            self = cls(
                name, glyphs, color=layerinfo.get("color"), lib=layerinfo.get("lib")
            )

        return self

    def unlazify(self) -> None:
        """Load all glyphs into memory."""
        for _ in self:
            pass

    __deepcopy__ = _deepcopy_unlazify_attrs

    def __contains__(self, name: object) -> bool:
        return name in self._glyphs

    def __delitem__(self, name: str) -> None:
        del self._glyphs[name]

    def __getitem__(self, name: str) -> Glyph:
        glyph_object = self._glyphs[name]
        if isinstance(glyph_object, Placeholder):
            return self.loadGlyph(name)
        return glyph_object

    def __setitem__(self, name: str, glyph: Glyph) -> None:
        if not isinstance(glyph, Glyph):
            raise TypeError(f"Expected Glyph, found {type(glyph).__name__}")
        glyph._name = name
        self._glyphs[name] = glyph

    def __iter__(self) -> Iterator[Glyph]:
        for name in self._glyphs:
            yield self[name]

    def __len__(self) -> int:
        return len(self._glyphs)

    def __repr__(self) -> str:
        n = len(self._glyphs)
        return "<{}.{} '{}' ({}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            self._name,
            "empty" if n == 0 else "{} glyph{}".format(n, "s" if n > 1 else ""),
            hex(id(self)),
        )

    def get(self, name: str, default: Optional[T] = None) -> Union[Optional[T], Glyph]:
        """Return the Glyph object for name if it is present in this layer,
        otherwise return ``default``."""
        try:
            return self[name]
        except KeyError:
            return default

    def keys(self) -> KeysView[str]:
        """Returns a list of glyph names."""
        return self._glyphs.keys()

    @overload
    def pop(self, key: str) -> Glyph:
        ...

    @overload
    def pop(self, key: str, default: Union[Glyph, T] = ...) -> Union[Glyph, T]:
        ...

    def pop(self, key: str, default: Union[Glyph, T] = KeyError) -> Union[Glyph, T]:  # type: ignore
        """Remove and return glyph from layer.

        Args:
            key: The name of the glyph.
            default: What to return if there is no glyph with the given name.
        """
        # NOTE: We can't defer to self._glyphs.pop because we must load glyphs
        try:
            glyph = self[key]
        except KeyError:
            if default is KeyError:
                raise
            glyph = default  # type: ignore
        else:
            del self[key]
        return glyph

    @property
    def name(self) -> str:
        """The name of the layer."""
        return self._name

    @property
    def bounds(self) -> Optional[BoundingBox]:
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the layer,
        taking the actual contours into account.

        |defcon_compat|
        """
        bounds = None
        for glyph in self:
            bounds = unionBounds(bounds, glyph.getBounds(self))
        return bounds

    @property
    def controlPointBounds(self) -> Optional[BoundingBox]:
        """Returns the (xMin, yMin, xMax, yMax) bounding box of the layer,
        taking only the control points into account.

        |defcon_compat|
        """
        bounds = None
        for glyph in self:
            bounds = unionBounds(bounds, glyph.getControlBounds(self))
        return bounds

    def addGlyph(self, glyph: Glyph) -> None:
        """Appends glyph object to the this layer unless its name is already
        taken."""
        self.insertGlyph(glyph, overwrite=False, copy=False)

    def insertGlyph(
        self,
        glyph: Glyph,
        name: Optional[str] = None,
        overwrite: bool = True,
        copy: bool = True,
    ) -> None:
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

    def loadGlyph(self, name: str) -> Glyph:
        """Load and return Glyph object."""
        # XXX: Remove and let __getitem__ do it?
        layer_path: Path = self._glyphSet.path
        glif_path = layer_path / self._glyphSet.contents[name]
        self._glyphs[name] = glyph = _read_glyph(glif_path, name)
        return glyph

    def newGlyph(self, name: str) -> Glyph:
        """Creates and returns new Glyph object in this layer with name."""
        if name in self._glyphs:
            raise KeyError(f"glyph named '{name}' already exists")
        self._glyphs[name] = glyph = Glyph(name)
        return glyph

    def renameGlyph(self, name: str, newName: str, overwrite: bool = False) -> None:
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

    def instantiateGlyphObject(self) -> Glyph:
        """Returns a new Glyph instance.

        |defcon_compat|
        """
        return Glyph()

    # where does writer glyphset come from? same as layer._glyphSet?
    def write(self, glyphSet: GlyphSet, saveAs: bool = True) -> None:
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
            if isinstance(glyph, Placeholder):
                if saveAs:
                    glyph = self.loadGlyph(name)
                else:
                    continue
            _prune_object_libs(glyph.lib, _fetch_glyph_identifiers(glyph))
            glyphSet.writeGlyph(
                name, glyphObject=glyph, drawPointsFunc=glyph.drawPoints
            )
        glyphSet.writeContents()
        glyphSet.writeLayerInfo(self)
        if saveAs:
            # all glyphs are loaded by now, no need to keep ref to glyphSet
            self._glyphSet = None


def _fetch_glyph_identifiers(glyph: Glyph) -> Set[str]:
    """Returns all identifiers in use in a glyph."""

    identifiers = set()
    for anchor in glyph.anchors:
        if anchor.identifier is not None:
            identifiers.add(anchor.identifier)
    for guideline in glyph.guidelines:
        if guideline.identifier is not None:
            identifiers.add(guideline.identifier)
    for contour in glyph.contours:
        if contour.identifier is not None:
            identifiers.add(contour.identifier)
        for point in contour:
            if point.identifier is not None:
                identifiers.add(point.identifier)
    for component in glyph.components:
        if component.identifier is not None:
            identifiers.add(component.identifier)
    return identifiers


def _read_glyph(glif_path: str, name: str) -> Glyph:
    # data = pickle.loads(readwrite_ufo_glif.read_glyph(glif_path))
    data = readwrite_ufo_glif.read_glyph(str(glif_path))
    return Glyph(
        name,
        height=data.get("height", 0),
        width=data.get("width", 0),
        unicodes=data.get("unicodes", []),
        image=Image(**data["image"]) if "image" in data else Image(),
        anchors=[Anchor(**kwargs) for kwargs in data.get("anchors", [])],
        guidelines=[Guideline(**kwargs) for kwargs in data.get("guidelines", [])],
        lib=data.get("lib", {}),
        note=data.get("note", {}),
        contours=[
            Contour(
                points=[Point(**kwargs) for kwargs in contour["points"]],
                identifier=contour.get("identifier"),
            )
            for contour in data.get("contours", [])
        ],
        components=[Component(**kwargs) for kwargs in data.get("components", [])],
    )


def _read_layer(layer_path: str) -> Tuple[Dict[str, Glyph], Dict[str, Any]]:
    # all_data: Dict[str, Dict[str, Any]] = pickle.loads(readwrite_ufo_glif.read_layer(layer_path))
    all_data: Dict[str, Dict[str, Any]]
    layerinfo: Dict[str, Any]
    all_data, layerinfo = readwrite_ufo_glif.read_layer(str(layer_path))

    glyphs = {
        name: Glyph(
            name,
            height=data.get("height", 0),
            width=data.get("width", 0),
            unicodes=data.get("unicodes", []),
            image=Image(**data["image"]) if "image" in data else Image(),
            anchors=[Anchor(**kwargs) for kwargs in data.get("anchors", [])],
            guidelines=[Guideline(**kwargs) for kwargs in data.get("guidelines", [])],
            lib=data.get("lib", {}),
            note=data.get("note", {}),
            contours=[
                Contour(
                    points=[Point(**kwargs) for kwargs in contour["points"]],
                    identifier=contour.get("identifier"),
                )
                for contour in data.get("contours", [])
            ],
            components=[Component(**kwargs) for kwargs in data.get("components", [])],
        )
        for name, data in all_data.items()
    }

    return glyphs, layerinfo
