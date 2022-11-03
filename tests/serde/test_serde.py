import importlib
import sys
from typing import Any, Dict, List

import pytest
from attrs import define

import ufoLib2.objects
from ufoLib2.serde import _SERDE_FORMATS_, serde


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


BASIC_EMPTY_OBJECTS: List[Dict[str, Any]] = [
    {"class_name": "Anchor", "args": (0, 0)},
    {"class_name": "Component", "args": ("a",)},
    {"class_name": "Contour", "args": ()},
    {"class_name": "DataSet", "args": ()},
    {"class_name": "Features", "args": ()},
    {"class_name": "Font", "args": ()},
    {"class_name": "Glyph", "args": ()},
    {"class_name": "Guideline", "args": (1,)},
    {"class_name": "Image", "args": ()},
    {"class_name": "ImageSet", "args": ()},
    {"class_name": "Info", "args": ()},
    {"class_name": "Kerning", "args": ()},
    {"class_name": "Layer", "args": ()},
    {
        "class_name": "LayerSet",
        "args": ({"public.default": ufoLib2.objects.Layer()},),
    },
    {"class_name": "Lib", "args": ()},
    {"class_name": "Point", "args": (2, 3)},
]
assert {d["class_name"] for d in BASIC_EMPTY_OBJECTS} == set(ufoLib2.objects.__all__)


@pytest.mark.parametrize("fmt", _SERDE_FORMATS_)
@pytest.mark.parametrize(
    "object_info",
    BASIC_EMPTY_OBJECTS,
    ids=lambda x: x["class_name"],  # type: ignore
)
def test_serde_all_objects(fmt: str, object_info: Dict[str, Any]) -> None:
    if fmt in ("json", "msgpack"):
        # skip these format tests if cattrs is not installed
        pytest.importorskip("cattrs")

    klass = getattr(ufoLib2.objects, object_info["class_name"])
    loads = getattr(klass, f"{fmt}_loads")
    obj = klass(*object_info["args"])
    dumps = getattr(obj, f"{fmt}_dumps")
    obj2 = loads(dumps())
    assert obj == obj2
