from __future__ import annotations

from typing import TYPE_CHECKING, Type

from attr import define

if TYPE_CHECKING:
    from cattr import GenConverter


@define
class Features:
    """A data class representing UFO features.

    See http://unifiedfontobject.org/versions/ufo3/features.fea/.
    """

    text: str = ""
    """Holds the content of the features.fea file."""

    def __bool__(self) -> bool:
        return bool(self.text)

    def __str__(self) -> str:
        return self.text

    def _unstructure(self, converter: GenConverter) -> str:
        del converter  # unused
        return self.text

    @staticmethod
    def _structure(data: str, cls: Type[Features], converter: GenConverter) -> Features:
        del converter  # unused
        return cls(data)
