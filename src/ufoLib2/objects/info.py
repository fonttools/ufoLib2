from __future__ import annotations

from enum import IntEnum
from typing import Any, Sequence, TypeVar

import attr
from attr import define, field
from fontTools.ufoLib import UFOReader

from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.misc import AttrDictMixin

__all__ = ("Info", "GaspRangeRecord", "NameRecord", "WidthClass")


def _positive(instance: Any, attribute: Any, value: int) -> None:
    if value < 0:
        raise ValueError(
            "'{name}' must be at least 0 (got {value!r})".format(
                name=attribute.name, value=value
            )
        )


_optional_positive = attr.validators.optional(_positive)


# or maybe use IntFlag?
class GaspBehavior(IntEnum):
    GRIDFIT = 0
    DOGRAY = 1
    SYMMETRIC_GRIDFIT = 2
    SYMMETRIC_SMOOTHING = 3


def _convert_GaspBehavior(seq: Sequence[GaspBehavior | int]) -> list[GaspBehavior]:
    return [v if isinstance(v, GaspBehavior) else GaspBehavior(v) for v in seq]


@define
class GaspRangeRecord(AttrDictMixin):
    rangeMaxPPEM: int = field(validator=_positive)
    # Use Set[GaspBehavior] instead of List?
    rangeGaspBehavior: list[GaspBehavior] = field(converter=_convert_GaspBehavior)


@define
class NameRecord(AttrDictMixin):
    nameID: int = field(validator=_positive)
    platformID: int = field(validator=_positive)
    encodingID: int = field(validator=_positive)
    languageID: int = field(validator=_positive)
    string: str = ""


class WidthClass(IntEnum):
    ULTRA_CONDENSED = 1
    EXTRA_CONDESED = 2
    CONDENSED = 3
    SEMI_CONDENSED = 4
    NORMAL = 5  # alias for WidthClass.MEDIUM
    MEDIUM = 5
    SEMI_EXPANDED = 6
    EXPANDED = 7
    EXTRA_EXPANDED = 8
    ULTRA_EXPANDED = 9


Tc = TypeVar("Tc", Guideline, GaspRangeRecord, NameRecord)


def _convert_optional_list(
    lst: Sequence[Any] | None, klass: type[Tc]
) -> list[Tc] | None:
    if lst is None:
        return None
    result = []
    for d in lst:
        if isinstance(d, klass):
            result.append(d)
        else:
            result.append(klass(**d))
    return result


def _convert_guidelines(
    values: Sequence[Guideline | Any] | None,
) -> list[Guideline] | None:
    return _convert_optional_list(values, Guideline)


def _convert_gasp_range_records(
    values: Sequence[GaspRangeRecord | Any] | None,
) -> list[GaspRangeRecord] | None:
    return _convert_optional_list(values, GaspRangeRecord)


def _convert_name_records(
    values: Sequence[NameRecord | Any] | None,
) -> list[NameRecord] | None:
    return _convert_optional_list(values, NameRecord)


def _convert_WidthClass(value: int | None) -> WidthClass | None:
    return None if value is None else WidthClass(value)


@define
class Info:
    """A data class representing the contents of fontinfo.plist.

    The attributes are formally specified at
    http://unifiedfontobject.org/versions/ufo3/fontinfo.plist/. Value validation is
    mostly done during saving and loading.
    """

    familyName: str | None = None
    styleName: str | None = None
    styleMapFamilyName: str | None = None
    styleMapStyleName: str | None = None
    versionMajor: int | None = field(default=None, validator=_optional_positive)
    versionMinor: int | None = field(default=None, validator=_optional_positive)

    copyright: str | None = None
    trademark: str | None = None

    unitsPerEm: float | None = field(default=None, validator=_optional_positive)
    descender: float | None = None
    xHeight: float | None = None
    capHeight: float | None = None
    ascender: float | None = None
    italicAngle: float | None = None

    note: str | None = None

    _guidelines: list[Guideline] | None = field(
        default=None, converter=_convert_guidelines
    )

    @property
    def guidelines(self) -> list[Guideline] | None:
        return self._guidelines

    @guidelines.setter
    def guidelines(self, value: list[Guideline] | None) -> None:
        self._guidelines = _convert_guidelines(value)

    _openTypeGaspRangeRecords: list[GaspRangeRecord] | None = field(
        default=None, converter=_convert_gasp_range_records
    )

    @property
    def openTypeGaspRangeRecords(self) -> list[GaspRangeRecord] | None:
        return self._openTypeGaspRangeRecords

    @openTypeGaspRangeRecords.setter
    def openTypeGaspRangeRecords(self, value: list[GaspRangeRecord] | None) -> None:
        self._openTypeGaspRangeRecords = _convert_gasp_range_records(value)

    openTypeHeadCreated: str | None = None
    openTypeHeadLowestRecPPEM: int | None = field(
        default=None, validator=_optional_positive
    )
    openTypeHeadFlags: list[int] | None = None

    openTypeHheaAscender: int | None = None
    openTypeHheaDescender: int | None = None
    openTypeHheaLineGap: int | None = None
    openTypeHheaCaretSlopeRise: int | None = None
    openTypeHheaCaretSlopeRun: int | None = None
    openTypeHheaCaretOffset: int | None = None

    openTypeNameDesigner: str | None = None
    openTypeNameDesignerURL: str | None = None
    openTypeNameManufacturer: str | None = None
    openTypeNameManufacturerURL: str | None = None
    openTypeNameLicense: str | None = None
    openTypeNameLicenseURL: str | None = None
    openTypeNameVersion: str | None = None
    openTypeNameUniqueID: str | None = None
    openTypeNameDescription: str | None = None
    openTypeNamePreferredFamilyName: str | None = None
    openTypeNamePreferredSubfamilyName: str | None = None
    openTypeNameCompatibleFullName: str | None = None
    openTypeNameSampleText: str | None = None
    openTypeNameWWSFamilyName: str | None = None
    openTypeNameWWSSubfamilyName: str | None = None

    _openTypeNameRecords: list[NameRecord] | None = field(
        default=None, converter=_convert_name_records
    )

    @property
    def openTypeNameRecords(self) -> list[NameRecord] | None:
        return self._openTypeNameRecords

    @openTypeNameRecords.setter
    def openTypeNameRecords(self, value: list[NameRecord] | None) -> None:
        self._openTypeNameRecords = _convert_name_records(value)

    _openTypeOS2WidthClass: WidthClass | None = field(
        default=None, converter=_convert_WidthClass
    )

    @property
    def openTypeOS2WidthClass(self) -> WidthClass | None:
        return self._openTypeOS2WidthClass

    @openTypeOS2WidthClass.setter
    def openTypeOS2WidthClass(self, value: WidthClass | None) -> None:
        self._openTypeOS2WidthClass = value if value is None else WidthClass(value)

    openTypeOS2WeightClass: int | None = field(default=None)

    @openTypeOS2WeightClass.validator
    def _validate_weight_class(self, attribute: Any, value: int | None) -> None:
        if value is not None and (value < 1 or value > 1000):
            raise ValueError("'openTypeOS2WeightClass' must be between 1 and 1000")

    openTypeOS2Selection: list[int] | None = None
    openTypeOS2VendorID: str | None = None
    openTypeOS2Panose: list[int] | None = None
    openTypeOS2FamilyClass: list[int] | None = None
    openTypeOS2UnicodeRanges: list[int] | None = None
    openTypeOS2CodePageRanges: list[int] | None = None
    openTypeOS2TypoAscender: int | None = None
    openTypeOS2TypoDescender: int | None = None
    openTypeOS2TypoLineGap: int | None = None
    openTypeOS2WinAscent: int | None = field(default=None, validator=_optional_positive)
    openTypeOS2WinDescent: int | None = field(
        default=None, validator=_optional_positive
    )
    openTypeOS2Type: list[int] | None = None
    openTypeOS2SubscriptXSize: int | None = None
    openTypeOS2SubscriptYSize: int | None = None
    openTypeOS2SubscriptXOffset: int | None = None
    openTypeOS2SubscriptYOffset: int | None = None
    openTypeOS2SuperscriptXSize: int | None = None
    openTypeOS2SuperscriptYSize: int | None = None
    openTypeOS2SuperscriptXOffset: int | None = None
    openTypeOS2SuperscriptYOffset: int | None = None
    openTypeOS2StrikeoutSize: int | None = None
    openTypeOS2StrikeoutPosition: int | None = None

    openTypeVheaVertTypoAscender: int | None = None
    openTypeVheaVertTypoDescender: int | None = None
    openTypeVheaVertTypoLineGap: int | None = None
    openTypeVheaCaretSlopeRise: int | None = None
    openTypeVheaCaretSlopeRun: int | None = None
    openTypeVheaCaretOffset: int | None = None

    postscriptFontName: str | None = None
    postscriptFullName: str | None = None
    postscriptSlantAngle: float | None = None
    postscriptUniqueID: int | None = None
    postscriptUnderlineThickness: float | None = None
    postscriptUnderlinePosition: float | None = None
    postscriptIsFixedPitch: bool | None = None
    postscriptBlueValues: list[float] | None = None
    postscriptOtherBlues: list[float] | None = None
    postscriptFamilyBlues: list[float] | None = None
    postscriptFamilyOtherBlues: list[float] | None = None
    postscriptStemSnapH: list[float] | None = None
    postscriptStemSnapV: list[float] | None = None
    postscriptBlueFuzz: float | None = None
    postscriptBlueShift: float | None = None
    postscriptBlueScale: float | None = None
    postscriptForceBold: bool | None = None
    postscriptDefaultWidthX: float | None = None
    postscriptNominalWidthX: float | None = None
    postscriptWeightName: str | None = None
    postscriptDefaultCharacter: str | None = None
    postscriptWindowsCharacterSet: str | None = None

    # old stuff
    macintoshFONDName: str | None = None
    macintoshFONDFamilyID: int | None = None
    year: int | None = None

    @classmethod
    def read(cls, reader: UFOReader) -> Info:
        """Instantiates a Info object from a
        :class:`fontTools.ufoLib.UFOReader`."""
        self = cls()
        reader.readInfo(self)
        return self
