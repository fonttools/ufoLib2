from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Union, cast

from ufoLib2.constants import DATA_LIB_KEY
from ufoLib2.serde import serde

if TYPE_CHECKING:
    from typing import Type

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


def _unstructure_data(value: Any, converter: Converter) -> Any:
    if isinstance(value, bytes):
        return {"type": DATA_LIB_KEY, "data": converter.unstructure(value)}
    elif isinstance(value, (list, tuple)):
        return [_unstructure_data(v, converter) for v in value]
    elif isinstance(value, Mapping):
        return {k: _unstructure_data(v, converter) for k, v in value.items()}
    return value


def _structure_data_inplace(
    key: Union[int, str], value: Any, container: Any, converter: Converter
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
class Lib(Dict[str, Any]):
    def _unstructure(self, converter: Converter) -> dict[str, Any]:
        # avoid encoding if converter supports bytes natively
        test = converter.unstructure(b"\0")
        if isinstance(test, bytes):
            return dict(self)
        elif not isinstance(test, str):
            raise NotImplementedError(type(test))

        data: dict[str, Any] = _unstructure_data(self, converter)
        return data

    @staticmethod
    def _structure(
        data: Mapping[str, Any],
        cls: Type[Lib],
        converter: Converter,
    ) -> Lib:
        self = cls(data)
        for k, v in self.items():
            _structure_data_inplace(k, v, self, converter)
        return self
