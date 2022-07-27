import importlib
import sys
from typing import Any

import pytest
from attrs import define

from ufoLib2.serde import serde


def test_raise_import_error(monkeypatch: Any) -> None:
    # pretent we can't import the module (e.g. msgpack not installed)
    monkeypatch.setitem(sys.modules, "ufoLib2.serde.msgpack", None)

    with pytest.raises(ImportError, match="ufoLib2.serde.msgpack"):
        importlib.import_module("ufoLib2.serde.msgpack")

    @serde
    @define
    class Foo:
        a: int
        b: str = "bar"

    foo = Foo(1)

    with pytest.raises(ImportError, match="ufoLib2.serde.msgpack"):
        # since the method is only added dynamicall at runtime, mypy complains that
        # "Foo" has no attribute "msgpack_dumps" -- so I shut it up
        foo.msgpack_dumps()  # type: ignore
