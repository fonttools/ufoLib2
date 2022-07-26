from __future__ import annotations

import pickle
from typing import Any, Type

from ufoLib2.typing import T


def dumps(obj: Any, **kwargs: Any) -> bytes:
    return pickle.dumps(obj, **kwargs)


def loads(s: bytes, object_class: Type[T], **kwargs: Any) -> T:
    obj = pickle.loads(s, **kwargs)
    assert isinstance(obj, object_class)
    return obj
