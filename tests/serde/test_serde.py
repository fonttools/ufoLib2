import importlib
from typing import Any, Dict, List

import pytest
from attrs import define

import ufoLib2.objects
from ufoLib2.errors import ExtrasNotInstalledError
from ufoLib2.serde import _SERDE_FORMATS_, serde

cattrs = None
try:
    import cattrs  # type: ignore
except ImportError:
    pass


msgpack = None
try:
    import msgpack  # type: ignore
except ImportError:
    pass


EXTRAS_REQUIREMENTS = {
    "json": ["cattrs"],
    "msgpack": ["cattrs", "msgpack"],
}


def assert_extras_not_installed(extras: str, missing_dependency: str) -> None:
    # sanity check that the dependency is not installed
    with pytest.raises(ImportError, match=missing_dependency):
        importlib.import_module(missing_dependency)

    @serde
    @define
    class Foo:
        a: int
        b: str = "bar"

    foo = Foo(1)

    with pytest.raises(
        ExtrasNotInstalledError, match=rf"Extras not installed: ufoLib2\[{extras}\]"
    ) as exc_info:
        dumps_method = getattr(foo, f"{extras}_dumps")
        dumps_method()

    assert isinstance(exc_info.value.__cause__, ModuleNotFoundError)


@pytest.mark.skipif(cattrs is not None, reason="cattrs installed, not applicable")
def test_json_cattrs_not_installed() -> None:
    assert_extras_not_installed("json", "cattrs")


@pytest.mark.skipif(cattrs is not None, reason="cattrs installed, not applicable")
def test_msgpack_cattrs_not_installed() -> None:
    assert_extras_not_installed("msgpack", "cattrs")


@pytest.mark.skipif(msgpack is not None, reason="msgpack installed, not applicable")
def test_msgpack_not_installed() -> None:
    assert_extras_not_installed("msgpack", "msgpack")


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
    ids=lambda x: x["class_name"],
)
def test_serde_all_objects(fmt: str, object_info: Dict[str, Any]) -> None:
    for req in EXTRAS_REQUIREMENTS[fmt]:
        pytest.importorskip(req)

    klass = getattr(ufoLib2.objects, object_info["class_name"])
    loads = getattr(klass, f"{fmt}_loads")
    obj = klass(*object_info["args"])
    dumps = getattr(obj, f"{fmt}_dumps")
    obj2 = loads(dumps())
    assert obj == obj2
