from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar, cast, overload

from ufoLib2.constants import DATA_LIB_KEY
from ufoLib2.serde import serde

if TYPE_CHECKING:

    from cattrs import Converter

# unfortunately mypy is not smart enough to support recursive types like plist...
# PlistEncodable = Union[
#     bool,
#     bytes,
#     datetime,
#     float,
#     int,
#     str,
#     Mapping[str, PlistEncodable],
#     Sequence[PlistEncodable],
# ]


def _convert_Lib(value: Mapping[str, Any]) -> Lib:
    return value if isinstance(value, Lib) else Lib(value)


# getter/setter properties used by Font, Layer, Glyph
def _get_lib(self: Any) -> Lib:
    return cast(Lib, self._lib)


def _set_lib(self: Any, value: Mapping[str, Any]) -> None:
    self._lib = _convert_Lib(value)


def _get_tempLib(self: Any) -> Lib:
    return cast(Lib, self._tempLib)


def _set_tempLib(self: Any, value: Mapping[str, Any]) -> None:
    self._tempLib = _convert_Lib(value)


def is_data_dict(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and "type" in value
        and value["type"] == DATA_LIB_KEY
        and "data" in value
    )


PlistScalar: TypeAlias = bool | datetime | float | int | str
PlistContainer: TypeAlias = (
    Mapping[str, PlistScalar] | list[PlistScalar] | tuple[PlistScalar, ...]
)
PlistEncodable: TypeAlias = (
    Mapping[str, PlistContainer] | list[PlistContainer] | tuple[PlistContainer, ...]
)

形PlistScalar = TypeVar("形PlistScalar", bool, datetime, float, int, str)
形PlistContainer = TypeVar(
    "形PlistContainer",
    Mapping[str, PlistScalar],
    list[PlistScalar],
    tuple[PlistScalar, ...],
)
形PlistEncodable = TypeVar(
    "形PlistEncodable",
    Mapping[str, PlistContainer],
    list[PlistContainer],
    tuple[PlistContainer, ...],
)


@overload
def _unstructure_data(value: bytes, converter: Converter) -> dict[str, PlistScalar]: ...


@overload
def _unstructure_data(
    value: list[PlistEncodable], converter: Converter
) -> list[PlistEncodable]: ...


@overload
def _unstructure_data(
    value: tuple[PlistEncodable, ...], converter: Converter
) -> list[PlistEncodable]: ...


@overload
def _unstructure_data(
    value: Mapping[str, PlistEncodable], converter: Converter
) -> dict[str, PlistEncodable]: ...


@overload
def _unstructure_data(value: 形PlistScalar, converter: Converter) -> 形PlistScalar: ...


def _unstructure_data(
    value: (
        bytes
        | list[PlistEncodable]
        | tuple[PlistEncodable, ...]
        | Mapping[str, PlistEncodable]
        | 形PlistScalar
    ),
    converter: Converter,
) -> (
    dict[str, PlistScalar]
    | list[PlistEncodable]
    | dict[str, PlistEncodable]
    | 形PlistScalar
):
    recurse: partial[PlistEncodable] = partial(_unstructure_data, converter=converter)
    if isinstance(value, bytes):
        return {"type": DATA_LIB_KEY, "data": converter.unstructure(value)}
    elif isinstance(value, (list, tuple)):
        return list(map(recurse, value))
    elif isinstance(value, Mapping):
        kk = tuple(value.keys())
        vv = tuple(value.values())
        rr = tuple(map(recurse, vv))
        return dict(zip(kk, rr, strict=True))
    return value


def _structure_data_inplace(
    key: int | str, value: Any, container: Any, converter: Converter
) -> None:
    if isinstance(value, list):
        for i, v in enumerate(value):
            _structure_data_inplace(i, v, value, converter)
    elif is_data_dict(value):
        container[key] = converter.structure(value["data"], bytes)
    elif isinstance(value, Mapping):
        for k, v in value.items():
            _structure_data_inplace(k, v, value, converter)


@serde
class Lib(dict[str, Any]):
    def _unstructure(
        self, converter: Converter
    ) -> dict[str, bytes | PlistEncodable] | dict[str, PlistEncodable]:
        # avoid encoding if converter supports bytes natively
        test: bytes | str | object = converter.unstructure(b"\0")
        if isinstance(test, bytes):
            return dict(self)
        elif not isinstance(test, str):
            raise NotImplementedError(type(test))

        data: dict[str, PlistEncodable] = _unstructure_data(self, converter)
        return data

    @staticmethod
    def _structure(
        data: Mapping[str, Any],
        cls: type[Lib],
        converter: Converter,
    ) -> Lib:
        self = cls(data)
        for k, v in self.items():
            _structure_data_inplace(k, v, self, converter)
        return self
