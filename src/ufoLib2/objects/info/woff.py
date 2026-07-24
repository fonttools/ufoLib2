"""Fontinfo.plist fields for WOFF 1.0 metadata.

https://unifiedfontobject.org/versions/ufo3/fontinfo.plist/#woff-data
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from attrs import Attribute, define, field

from ufoLib2.objects.misc import AttrDictMixin

_T = TypeVar("_T", bound=AttrDictMixin)


def _convert_list_of_woff_metadata(
    cls: type[_T], values: Sequence[_T | Mapping[str, Any]]
) -> list[_T]:
    return [cls.coerce_from_dict(v) for v in values]


@define
class WoffMetadataUniqueID(AttrDictMixin):
    id: str


@define
class WoffMetadataVendor(AttrDictMixin):
    name: str
    url: str | None = None
    dir: str | None = None
    # 'class' of course is reserved in Python
    class_: str | None = field(default=None, metadata={"rename_attr": "class"})


@define
class WoffMetadataCredit(AttrDictMixin):
    name: str
    url: str | None = None
    role: str | None = None
    dir: str | None = None
    class_: str | None = field(default=None, metadata={"rename_attr": "class"})


def _convert_list_of_woff_metadata_credits(
    value: list[WoffMetadataCredit | Mapping[str, Any]],
) -> list[WoffMetadataCredit]:
    return _convert_list_of_woff_metadata(WoffMetadataCredit, value)


@define
class WoffMetadataCredits(AttrDictMixin):
    credits: list[WoffMetadataCredit] = field(
        factory=list,
        converter=_convert_list_of_woff_metadata_credits,
    )


@define
class WoffMetadataText(AttrDictMixin):
    text: str
    language: str | None = None
    dir: str | None = None
    class_: str | None = field(default=None, metadata={"rename_attr": "class"})


def _at_least_one_item(
    self: Any, attribute: Attribute[Any], value: Sequence[Any]
) -> None:
    if len(value) == 0:
        raise ValueError(
            f"{self.__class__.__name__}.{attribute.name} must contain at list 1 item"
        )


def _convert_list_of_woff_metadata_texts(
    value: list[WoffMetadataText | Mapping[str, Any]],
) -> list[WoffMetadataText]:
    return _convert_list_of_woff_metadata(WoffMetadataText, value)


@define
class WoffMetadataDescription(AttrDictMixin):
    url: str | None = None
    text: list[WoffMetadataText] = field(
        factory=list,
        validator=_at_least_one_item,
        converter=_convert_list_of_woff_metadata_texts,
    )


@define
class WoffMetadataLicense(AttrDictMixin):
    url: str | None = None
    id: str | None = None
    text: list[WoffMetadataText] = field(
        factory=list,
        converter=_convert_list_of_woff_metadata_texts,
    )


@define
class WoffMetadataCopyright(AttrDictMixin):
    text: list[WoffMetadataText] = field(
        factory=list,
        validator=_at_least_one_item,
        converter=_convert_list_of_woff_metadata_texts,
    )


@define
class WoffMetadataTrademark(AttrDictMixin):
    text: list[WoffMetadataText] = field(
        factory=list,
        validator=_at_least_one_item,
        converter=_convert_list_of_woff_metadata_texts,
    )


@define
class WoffMetadataLicensee(AttrDictMixin):
    name: str
    dir: str | None = None
    class_: str | None = field(default=None, metadata={"rename_attr": "class"})


@define
class WoffMetadataExtensionName(AttrDictMixin):
    text: str
    language: str | None = None
    dir: str | None = None
    class_: str | None = field(default=None, metadata={"rename_attr": "class"})


@define
class WoffMetadataExtensionValue(AttrDictMixin):
    text: str
    language: str | None = None
    dir: str | None = None
    class_: str | None = field(default=None, metadata={"rename_attr": "class"})


def _convert_list_of_woff_metadata_extension_name(
    value: list[WoffMetadataExtensionName | Mapping[str, Any]],
) -> list[WoffMetadataExtensionName]:
    return _convert_list_of_woff_metadata(WoffMetadataExtensionName, value)


def _convert_list_of_woff_metadata_extension_value(
    value: list[WoffMetadataExtensionValue | Mapping[str, Any]],
) -> list[WoffMetadataExtensionValue]:
    return _convert_list_of_woff_metadata(WoffMetadataExtensionValue, value)


@define
class WoffMetadataExtensionItem(AttrDictMixin):
    id: str | None = None
    names: list[WoffMetadataExtensionName] = field(
        factory=list,
        validator=_at_least_one_item,
        converter=_convert_list_of_woff_metadata_extension_name,
    )
    # 'values()' is the name of the dict method, hence the attribute named 'values_'
    values_: list[WoffMetadataExtensionValue] = field(
        factory=list,
        validator=_at_least_one_item,
        converter=_convert_list_of_woff_metadata_extension_value,
        metadata={"rename_attr": "values"},
    )


def _convert_list_of_woff_metadata_extension_item(
    value: list[WoffMetadataExtensionItem | Mapping[str, Any]],
) -> list[WoffMetadataExtensionItem]:
    return _convert_list_of_woff_metadata(WoffMetadataExtensionItem, value)


@define
class WoffMetadataExtension(AttrDictMixin):
    id: str | None
    names: list[WoffMetadataExtensionName] = field(
        factory=list,
        converter=_convert_list_of_woff_metadata_extension_name,
    )
    # 'items()' is the name of the dict method, hence the attribute named 'items_'
    items_: list[WoffMetadataExtensionItem] = field(
        factory=list,
        validator=_at_least_one_item,
        converter=_convert_list_of_woff_metadata_extension_item,
        metadata={"rename_attr": "items"},
    )
