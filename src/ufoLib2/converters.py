from __future__ import annotations

import sys
from functools import partial
from typing import Any, Callable, Tuple, Type, cast

import cattr.preconf.orjson
from attr import fields, has, resolve_types
from cattr import GenConverter
from cattr.gen import (
    AttributeOverride,
    make_dict_structure_fn,
    make_dict_unstructure_fn,
    override,
)
from fontTools.misc.transform import Transform

is_py37 = sys.version_info[:2] == (3, 7)

if is_py37:

    def get_origin(cl: Type[Any]) -> Any:
        return getattr(cl, "__origin__", None)


else:
    from typing import get_origin  # type: ignore


def is_ufoLib2_class(cls: Type[Any]) -> bool:
    mod: str = getattr(cls, "__module__", "")
    return mod.split(".")[0] == "ufoLib2"


def is_ufoLib2_attrs_class(cls: Type[Any]) -> bool:
    return is_ufoLib2_class(cls) and (has(cls) or has(get_origin(cls)))


def is_ufoLib2_class_with_custom_unstructure(cls: Type[Any]) -> bool:
    return is_ufoLib2_class(cls) and hasattr(cls, "_unstructure")


def is_ufoLib2_class_with_custom_structure(cls: Type[Any]) -> bool:
    return is_ufoLib2_class(cls) and hasattr(cls, "_structure")


def register_hooks(conv: GenConverter, allow_bytes: bool = True) -> None:
    def attrs_hook_factory(
        cls: Type[Any], gen_fn: Callable[..., Callable[[Any], Any]], structuring: bool
    ) -> Callable[[Any], Any]:
        base = get_origin(cls)
        if base is None:
            base = cls
        attribs = fields(base)
        if any(isinstance(a.type, str) for a in attribs):
            # PEP 563 annotations need to be resolved.
            # As of cattrs 1.8.0, make_dict_*_fn functions don't call resolve_types
            # so we need to do it ourselves:
            # https://github.com/python-attrs/cattrs/issues/169
            resolve_types(base)

        kwargs: dict[str, bool | AttributeOverride] = {}
        if structuring:
            kwargs["_cattrs_forbid_extra_keys"] = conv.forbid_extra_keys
            kwargs["_cattrs_prefer_attrib_converters"] = conv._prefer_attrib_converters
        else:
            kwargs["omit_if_default"] = conv.omit_if_default
        for a in attribs:
            if not a.init:
                kwargs[a.name] = override(omit=True)
            elif a.name[0] == "_":
                kwargs[a.name] = override(
                    omit_if_default=a.metadata.get(
                        "omit_if_default", conv.omit_if_default
                    ),
                    rename=a.name[1:],
                )
            elif "omit_if_default" in a.metadata:
                kwargs[a.name] = override(omit_if_default=a.metadata["omit_if_default"])
            elif a.type in conv.type_overrides:
                kwargs[a.name] = conv.type_overrides[a.type]

        return gen_fn(cls, conv, **kwargs)

    def custom_unstructure_hook_factory(cls: Type[Any]) -> Callable[[Any], Any]:
        return partial(cls._unstructure, converter=conv)

    def custom_structure_hook_factory(cls: Type[Any]) -> Callable[[Any], Any]:
        return partial(cls._structure, converter=conv)

    def unstructure_transform(t: Transform) -> Tuple[float]:
        return cast(Tuple[float], tuple(t))

    conv.register_unstructure_hook_factory(
        is_ufoLib2_attrs_class,
        partial(attrs_hook_factory, gen_fn=make_dict_unstructure_fn, structuring=False),
    )
    conv.register_unstructure_hook_factory(
        is_ufoLib2_class_with_custom_unstructure,
        custom_unstructure_hook_factory,
    )
    conv.register_unstructure_hook(
        cast(Type[Transform], Transform), unstructure_transform
    )

    conv.register_structure_hook_factory(
        is_ufoLib2_attrs_class,
        partial(attrs_hook_factory, gen_fn=make_dict_structure_fn, structuring=True),
    )
    conv.register_structure_hook_factory(
        is_ufoLib2_class_with_custom_structure,
        custom_structure_hook_factory,
    )

    if not allow_bytes:
        from base64 import b64decode, b64encode

        def unstructure_bytes(v: bytes) -> str:
            return (b64encode(v) if v else b"").decode("utf8")

        def structure_bytes(v: str, _: Any) -> bytes:
            return b64decode(v)

        conv.register_unstructure_hook(bytes, unstructure_bytes)
        conv.register_structure_hook(bytes, structure_bytes)


json_converter = cattr.preconf.orjson.make_converter(
    omit_if_default=True,
    # 'forbid_extra_keys' conflicts with override(rename=...).
    # Re-enable once https://github.com/python-attrs/cattrs/issues/190 gets fixed
    # forbid_extra_keys=True,
    prefer_attrib_converters=False,
)
register_hooks(json_converter, allow_bytes=False)
