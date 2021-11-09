from __future__ import annotations

import collections.abc
import uuid
from abc import abstractmethod
from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterator, NamedTuple, Sequence, TypeVar, cast

import attr
from attr import define, field
from fontTools.misc.arrayTools import unionRect
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.ufoLib import UFOReader, UFOWriter

from ufoLib2.constants import OBJECT_LIBS_KEY
from ufoLib2.typing import Drawable, GlyphSet, HasIdentifier


class BoundingBox(NamedTuple):
    """Represents a bounding box as a tuple of (xMin, yMin, xMax, yMax)."""

    xMin: float
    yMin: float
    xMax: float
    yMax: float


def getBounds(drawable: Drawable, layer: GlyphSet | None) -> BoundingBox | None:
    pen = BoundsPen(layer)
    # raise 'KeyError' when a referenced component is missing from glyph set
    pen.skipMissingComponents = False
    drawable.draw(pen)
    return None if pen.bounds is None else BoundingBox(*pen.bounds)


def getControlBounds(drawable: Drawable, layer: GlyphSet | None) -> BoundingBox | None:
    pen = ControlBoundsPen(layer)
    # raise 'KeyError' when a referenced component is missing from glyph set
    pen.skipMissingComponents = False
    drawable.draw(pen)
    return None if pen.bounds is None else BoundingBox(*pen.bounds)


def unionBounds(
    bounds1: BoundingBox | None, bounds2: BoundingBox | None
) -> BoundingBox | None:
    if bounds1 is None:
        return bounds2
    if bounds2 is None:
        return bounds1
    return BoundingBox(*unionRect(bounds1, bounds2))


def _deepcopy_unlazify_attrs(self: Any, memo: Any) -> Any:
    if getattr(self, "_lazy", True) and hasattr(self, "unlazify"):
        self.unlazify()
    return self.__class__(
        **{
            (a.name if a.name[0] != "_" else a.name[1:]): deepcopy(
                getattr(self, a.name), memo
            )
            for a in attr.fields(self.__class__)
            if a.init and a.metadata.get("copyable", True)
        },
    )


def _object_lib(parent_lib: dict[str, Any], obj: HasIdentifier) -> dict[str, Any]:
    if obj.identifier is None:
        # Use UUID4 because it allows us to set a new identifier without
        # checking if it's already used anywhere else and be right most
        # of the time.
        obj.identifier = str(uuid.uuid4())

    object_libs: dict[str, Any]
    if "public.objectLibs" not in parent_lib:
        object_libs = parent_lib["public.objectLibs"] = {}
    else:
        object_libs = parent_lib["public.objectLibs"]
        assert isinstance(object_libs, collections.abc.MutableMapping)

    if obj.identifier in object_libs:
        object_lib: dict[str, Any] = object_libs[obj.identifier]
        return object_lib
    lib: dict[str, Any] = {}
    object_libs[obj.identifier] = lib
    return lib


def _prune_object_libs(parent_lib: dict[str, Any], identifiers: set[str]) -> None:
    """Prune non-existing objects and empty libs from a lib's
    public.objectLibs.

    Empty object libs are pruned, but object identifiers stay.
    """

    if OBJECT_LIBS_KEY not in parent_lib:
        return

    object_libs = parent_lib[OBJECT_LIBS_KEY]
    parent_lib[OBJECT_LIBS_KEY] = {
        k: v for k, v in object_libs.items() if k in identifiers and v
    }


class Placeholder:
    """Represents a sentinel value to signal a "lazy" object hasn't been loaded yet."""


_NOT_LOADED = Placeholder()


# Create a generic variable for mypy that can be 'DataStore' or any subclass.
Tds = TypeVar("Tds", bound="DataStore")

# For Python 3.7 compatibility.
if TYPE_CHECKING:
    DataStoreMapping = MutableMapping[str, bytes]
else:
    DataStoreMapping = MutableMapping


@define
class DataStore(DataStoreMapping):
    """Represents the base class for ImageSet and DataSet.

    Both behave like a dictionary that loads its "values" lazily by default and only
    differ in which reader and writer methods they call.
    """

    _data: dict[str, bytes | Placeholder] = field(factory=dict)

    _lazy: bool | None = field(default=False, kw_only=True, eq=False, init=False)
    _reader: UFOReader | None = field(default=None, init=False, repr=False, eq=False)
    _scheduledForDeletion: set[str] = field(
        factory=set, init=False, repr=False, eq=False
    )

    def __eq__(self, other: object) -> bool:
        # same as attrs-defined __eq__ method, only that it un-lazifies DataStores
        # if needed.
        # NOTE: Avoid isinstance check that mypy recognizes because we don't want to
        # test possible Font subclasses for equality.
        if other.__class__ is not self.__class__:
            return NotImplemented
        other = cast(DataStore, other)

        for data_store in (self, other):
            if data_store._lazy:
                data_store.unlazify()

        return self._data == other._data

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    @classmethod
    def read(cls: type[Tds], reader: UFOReader, lazy: bool = True) -> Tds:
        """Instantiate the data store from a :class:`fontTools.ufoLib.UFOReader`."""
        self = cls()
        for fileName in cls.list_contents(reader):
            if lazy:
                self._data[fileName] = _NOT_LOADED
            else:
                self._data[fileName] = cls.read_data(reader, fileName)
        self._lazy = lazy
        if lazy:
            self._reader = reader
        return self

    @staticmethod
    @abstractmethod
    def list_contents(reader: UFOReader) -> list[str]:
        """Returns a list of POSIX filename strings in the data store."""
        ...

    @staticmethod
    @abstractmethod
    def read_data(reader: UFOReader, filename: str) -> bytes:
        """Returns the data at filename within the store."""
        ...

    @staticmethod
    @abstractmethod
    def write_data(writer: UFOWriter, filename: str, data: bytes) -> None:
        """Writes the data to filename within the store."""
        ...

    @staticmethod
    @abstractmethod
    def remove_data(writer: UFOWriter, filename: str) -> None:
        """Remove the data at filename within the store."""
        ...

    def unlazify(self) -> None:
        """Load all data into memory."""
        if self._lazy:
            assert self._reader is not None
            for _ in self.items():
                pass
        self._lazy = False

    __deepcopy__ = _deepcopy_unlazify_attrs

    # MutableMapping methods

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __getitem__(self, fileName: str) -> bytes:
        data_object = self._data[fileName]
        if isinstance(data_object, Placeholder):
            data_object = self._data[fileName] = self.read_data(self._reader, fileName)
        return data_object

    def __setitem__(self, fileName: str, data: bytes) -> None:
        # should we forbid overwrite?
        self._data[fileName] = data
        if fileName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(fileName)

    def __delitem__(self, fileName: str) -> None:
        del self._data[fileName]
        self._scheduledForDeletion.add(fileName)

    def __repr__(self) -> str:
        n = len(self._data)
        return "<{}.{} ({}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            "empty" if n == 0 else "{} file{}".format(n, "s" if n > 1 else ""),
            hex(id(self)),
        )

    def write(self, writer: UFOWriter, saveAs: bool | None = None) -> None:
        """Write the data store to a :class:`fontTools.ufoLib.UFOWriter`."""
        if saveAs is None:
            saveAs = self._reader is not writer
        # if in-place, remove deleted data
        if not saveAs:
            for fileName in self._scheduledForDeletion:
                self.remove_data(writer, fileName)
        # Write data. Iterating over _data.items() prevents automatic loading.
        for fileName, data in self._data.items():
            # Two paths:
            # 1) We are saving in-place. Only write to disk what is loaded, it
            #    might be modified.
            # 2) We save elsewhere. Load all data files to write them back out.
            # XXX: Move write_data into `if saveAs` branch to simplify code?
            if isinstance(data, Placeholder):
                if saveAs:
                    data = self.read_data(self._reader, fileName)
                    self._data[fileName] = data
                else:
                    continue
            self.write_data(writer, fileName, data)
        self._scheduledForDeletion = set()
        if saveAs:
            # all data was read by now, ref to reader no longer needed
            self._reader = None

    @property
    def fileNames(self) -> list[str]:
        """Returns a list of filenames in the data store."""
        return list(self._data.keys())


# For Python 3.7 compatibility.
if TYPE_CHECKING:
    AttrDictMixinMapping = Mapping[str, Any]
else:
    AttrDictMixinMapping = Mapping


class AttrDictMixin(AttrDictMixinMapping):
    """Read attribute values using mapping interface.

    For use with Anchors and Guidelines classes, where client code
    expects them to behave as dict.
    """

    # XXX: Use generics?

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __iter__(self) -> Iterator[Any]:
        for key in attr.fields_dict(self.__class__):
            if getattr(self, key) is not None:
                yield key

    def __len__(self) -> int:
        return sum(1 for _ in self)


def _convert_transform(t: Transform | Sequence[float]) -> Transform:
    """Return a passed-in Transform as is, otherwise convert a sequence of
    numbers to a Transform if need be."""
    return t if isinstance(t, Transform) else Transform(*t)
