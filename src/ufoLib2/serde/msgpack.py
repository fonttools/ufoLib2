from __future__ import annotations

from typing import Any, Type, cast

import msgpack  # type: ignore

from ufoLib2.converters import binary_converter
from ufoLib2.typing import T


def dumps(obj: Any, **kwargs: Any) -> bytes:
    data = binary_converter.unstructure(obj)
    result = msgpack.packb(data, **kwargs)
    return cast(bytes, result)


def loads(s: bytes, object_class: Type[T], **kwargs: Any) -> T:
    data = msgpack.unpackb(s, **kwargs)
    return binary_converter.structure(data, object_class)
