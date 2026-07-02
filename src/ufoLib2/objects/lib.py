from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence
from datetime import datetime
from typing import Any, TypeAlias, cast

from cattrs import Converter
from typing_extensions import TypeIs

from ufoLib2.constants import DATA_LIB_KEY
from ufoLib2.serde import serde

PlistEncodable: TypeAlias = (
    bool
    | bytes
    | datetime
    | float
    | int
    | str
    | MutableMapping[str, "PlistEncodable"]
    | MutableSequence["PlistEncodable"]
)


# TODO if `Lib(value)` returns a `dict` subclass, then `value` can be `Mapping`, otherwise is must be
# `MutableMapping`.
def _convert_Lib(value: Mapping[str, PlistEncodable]) -> Lib:
    return value if isinstance(value, Lib) else Lib(value)


# getter/setter properties used by Font, Layer, Glyph
# TODO can we make `self: Any` more specific?
def _get_lib(self: Any) -> Lib:
    return cast(Lib, self._lib)


def _set_lib(self: Any, value: Mapping[str, PlistEncodable]) -> None:
    self._lib = _convert_Lib(value)


def _get_tempLib(self: Any) -> Lib:
    return cast(Lib, self._tempLib)


def _set_tempLib(self: Any, value: Mapping[str, PlistEncodable]) -> None:
    self._tempLib = _convert_Lib(value)


def is_data_dict(value: PlistEncodable) -> TypeIs[MutableMapping[str, PlistEncodable]]:
    return (
        isinstance(value, MutableMapping)
        and "type" in value
        and value["type"] == DATA_LIB_KEY
        and "data" in value
    )


def _unstructure_data(value: PlistEncodable, converter: Converter) -> PlistEncodable:
    if isinstance(value, bytes):
        return {"type": DATA_LIB_KEY, "data": converter.unstructure(value)}
    elif isinstance(value, MutableSequence):
        return list(_unstructure_data(v, converter) for v in value)
    elif isinstance(value, MutableMapping):
        return {k: _unstructure_data(v, converter) for k, v in value.items()}
    return value


# NOTE "inplace" requires `Mutable*`.
def _structure_data_inplace(
    key: int | str,
    value: PlistEncodable,
    container: MutableMapping[str, PlistEncodable] | MutableSequence[PlistEncodable],
    converter: Converter,
) -> None:
    if isinstance(value, MutableSequence):
        for i, v in enumerate(value):
            _structure_data_inplace(i, v, value, converter)
    # TODO I _feel_ like this shouldn't need 3 checks.
    elif (
        is_data_dict(value)
        and isinstance(key, str)
        and isinstance(container, MutableMapping)
    ):
        container[key] = converter.structure(value["data"], bytes)
    elif isinstance(value, MutableMapping):
        for k, v in value.items():
            _structure_data_inplace(k, v, value, converter)
    # TODO I _feel_ like `_structure_data_inplace` should "symmetrical" with `_unstructure_data`, but
    # `_structure_data_inplace` does not have an analog to `return value`. That makes me wonder if the
    # logic needs to be changed.


@serde
class Lib(dict[str, PlistEncodable]):
    def _unstructure(self, converter: Converter) -> PlistEncodable:
        # avoid encoding if converter supports bytes natively
        test: bytes | str | object = converter.unstructure(b"\0")
        if isinstance(test, bytes):
            return dict(self)
        elif not isinstance(test, str):
            raise NotImplementedError(type(test))

        return _unstructure_data(self, converter)

    @staticmethod
    def _structure(
        data: Mapping[str, PlistEncodable], cls: type[Lib], converter: Converter
    ) -> Lib:
        self: Lib = cls(data)
        for k, v in self.items():
            _structure_data_inplace(k, v, self, converter)
        return self
