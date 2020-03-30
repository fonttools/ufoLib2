from collections.abc import Mapping
from typing import Iterator, Optional, Tuple

import attr
from fontTools.misc.transform import Identity, Transform

from .misc import _convert_transform


@attr.s(auto_attribs=True, slots=True)
class Image(Mapping):
    fileName: Optional[str] = None
    transformation: Transform = attr.ib(default=Identity, converter=_convert_transform)
    color: Optional[str] = None

    def clear(self) -> None:
        self.fileName = None
        self.transformation = Identity
        self.color = None

    def __bool__(self) -> bool:
        # Glyph.image evaluates to False if no fileName is set
        return self.fileName is not None

    _transformation_keys_: Tuple[str, str, str, str, str, str] = (
        "xScale",
        "xyScale",
        "yxScale",
        "yScale",
        "xOffset",
        "yOffset",
    )
    _valid_keys_: Tuple[str, str, str, str, str, str, str, str] = (
        "fileName",
    ) + _transformation_keys_ + ("color",)

    # implementation of collections.abc.Mapping abstract methods.
    # the fontTools.ufoLib.validators.imageValidator requires that image is a
    # subclass of Mapping...

    def __getitem__(self, key):
        try:
            i = self._transformation_keys_.index(key)
        except ValueError:
            try:
                return getattr(self, key)
            except AttributeError:
                raise KeyError(key)
        else:
            return self.transformation[i]

    def __len__(self) -> int:
        return len(self._valid_keys_)

    def __iter__(self) -> Iterator[str]:
        return iter(self._valid_keys_)
