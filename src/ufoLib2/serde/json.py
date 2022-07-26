from __future__ import annotations

from typing import Any, Type, cast

from ufoLib2.converters import structure, unstructure
from ufoLib2.typing import T

have_orjson = False
try:
    import orjson as json  # type: ignore

    have_orjson = True
except ImportError:
    import json  # type: ignore


def dumps(
    obj: Any,
    indent: int | None = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> bytes:
    data = unstructure(obj)

    if have_orjson:
        if indent is not None:
            if indent != 2:
                raise ValueError("indent must be 2 or None for orjson")
            kwargs["option"] = kwargs.pop("option", 0) | json.OPT_INDENT_2
        if sort_keys:
            kwargs["option"] = kwargs.pop("option", 0) | json.OPT_SORT_KEYS
        # orjson.dumps always returns bytes
        result = json.dumps(data, **kwargs)
    else:
        # built-in json.dumps returns a string, not bytes, hence the encoding
        s = json.dumps(data, indent=indent, sort_keys=sort_keys, **kwargs)
        result = s.encode("utf-8")
    return cast(bytes, result)


def loads(s: str | bytes, object_class: Type[T], **kwargs: Any) -> T:
    data = json.loads(s, **kwargs)
    return structure(data, object_class)
