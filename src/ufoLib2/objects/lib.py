from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Mapping, Union, cast

import attr
from attr import field, frozen

from ufoLib2.constants import DATA_LIB_KEY
from ufoLib2.objects.misc import BYTES_ENCODINGS, DEFAULT_ENCODING

if TYPE_CHECKING:
    from typing import Type

    from cattr import GenConverter

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


def _check_encoding(_instance, _attribute, value):  # type: ignore
    if value not in BYTES_ENCODINGS:
        raise ValueError(f"Unsupported plist data encoding: {value!r}")


@frozen
class PlistData:
    """Adapter between plist binary <data> and json-encodable string."""

    type: ClassVar[str] = DATA_LIB_KEY
    data: str
    encoding: str = field(validator=_check_encoding)

    @classmethod
    def encode(cls, data: bytes, encoding: str = DEFAULT_ENCODING) -> "PlistData":
        encode, _ = BYTES_ENCODINGS[encoding]
        return cls(encode(data), encoding=encoding)

    def decode(self) -> bytes:
        _, decode = BYTES_ENCODINGS[self.encoding]
        return decode(self.data)

    def asdict(self) -> dict[str, str]:
        return {"type": self.type, **attr.asdict(self)}

    @staticmethod
    def is_data_dict(value: Any) -> bool:
        return (
            isinstance(value, Mapping)
            and "type" in value
            and value["type"] == DATA_LIB_KEY
            and "data" in value
            and "encoding" in value
        )

    @classmethod
    def fromdict(cls, data: Mapping[str, str]) -> "PlistData":
        try:
            assert data["type"] == DATA_LIB_KEY
            return cls(data["data"], data["encoding"])
        except (AssertionError, KeyError) as e:
            raise ValueError("Invalid serialized data dict: {data!r}") from e


def _serialize_data(value: Any) -> Any:
    if isinstance(value, bytes):
        return PlistData.encode(value).asdict()
    elif isinstance(value, (list, tuple)):
        return [_serialize_data(v) for v in value]
    elif isinstance(value, Mapping):
        return {k: _serialize_data(v) for k, v in value.items()}
    elif isinstance(value, PlistData):
        return value.asdict()
    return value


def _deserialize_data_inplace(key: Union[int, str], value: Any, container: Any) -> None:
    if isinstance(value, list):
        for i, v in enumerate(value):
            _deserialize_data_inplace(i, v, value)
    elif PlistData.is_data_dict(value):
        container[key] = PlistData.fromdict(value).decode()
    elif isinstance(value, Mapping):
        for k, v in value.items():
            _deserialize_data_inplace(k, v, value)
    elif isinstance(value, PlistData):
        container[key] = value.decode()


class Lib(Dict[str, Any]):
    def _unstructure(self, converter: GenConverter) -> dict[str, Any]:
        # avoid encoding if converter supports bytes natively
        if isinstance(converter.unstructure(b"\0"), bytes):
            return dict(self)

        data: dict[str, Any] = _serialize_data(self)
        return data

    @staticmethod
    def _structure(
        data: Mapping[str, Any],
        cls: Type[Lib],
        converter: GenConverter,
    ) -> Lib:
        del converter  # unused
        self = cls(data)
        for k, v in self.items():
            _deserialize_data_inplace(k, v, self)
        return self
