from enum import IntEnum
from typing import Any, List, Optional, Sequence, Union

import attr

from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.misc import AttrDictMixin
from ufoLib2.typing import Number

__all__ = ["Info", "GaspRangeRecord", "NameRecord", "WidthClass"]


def _positive(instance, attribute, value):
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


def _convert_GaspBehavior(
    seq: Sequence[Union[GaspBehavior, int]]
) -> List[GaspBehavior]:
    return [v if isinstance(v, GaspBehavior) else GaspBehavior(v) for v in seq]


@attr.s(auto_attribs=True, slots=True)
class GaspRangeRecord(AttrDictMixin):
    rangeMaxPPEM: int = attr.ib(validator=_positive)
    # Use Set[GaspBehavior] instead of List?
    rangeGaspBehavior: List[GaspBehavior] = attr.ib(converter=_convert_GaspBehavior)


@attr.s(auto_attribs=True, slots=True)
class NameRecord(AttrDictMixin):
    nameID: int = attr.ib(validator=_positive)
    platformID: int = attr.ib(validator=_positive)
    encodingID: int = attr.ib(validator=_positive)
    languageID: int = attr.ib(validator=_positive)
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


def _convert_optional_list(lst, klass):
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
    values: Optional[Sequence[Union[Guideline, Any]]]
) -> Optional[List[Guideline]]:
    return _convert_optional_list(values, Guideline)


def _convert_gasp_range_records(
    values: Optional[Sequence[Union[GaspRangeRecord, Any]]]
) -> Optional[List[GaspRangeRecord]]:
    return _convert_optional_list(values, GaspRangeRecord)


def _convert_name_records(
    values: Optional[Sequence[Union[NameRecord, Any]]]
) -> Optional[List[NameRecord]]:
    return _convert_optional_list(values, NameRecord)


def _convert_WidthClass(value: Optional[int]) -> Optional[WidthClass]:
    return None if value is None else WidthClass(value)


@attr.s(auto_attribs=True, slots=True)
class Info:
    familyName: Optional[str] = None
    styleName: Optional[str] = None
    styleMapFamilyName: Optional[str] = None
    styleMapStyleName: Optional[str] = None
    versionMajor: Optional[int] = attr.ib(default=None, validator=_optional_positive)
    versionMinor: Optional[int] = attr.ib(default=None, validator=_optional_positive)

    copyright: Optional[str] = None
    trademark: Optional[str] = None

    unitsPerEm: Optional[Number] = attr.ib(default=None, validator=_optional_positive)
    descender: Optional[Number] = None
    xHeight: Optional[Number] = None
    capHeight: Optional[Number] = None
    ascender: Optional[Number] = None
    italicAngle: Optional[Number] = None

    note: Optional[str] = None

    _guidelines: Optional[List[Guideline]] = attr.ib(
        default=None, converter=_convert_guidelines
    )

    @property
    def guidelines(self):
        return self._guidelines

    @guidelines.setter
    def guidelines(self, value):
        self._guidelines = _convert_guidelines(value)

    _openTypeGaspRangeRecords: Optional[List[GaspRangeRecord]] = attr.ib(
        default=None, converter=_convert_gasp_range_records,
    )

    @property
    def openTypeGaspRangeRecords(self):
        return self._openTypeGaspRangeRecords

    @openTypeGaspRangeRecords.setter
    def openTypeGaspRangeRecords(self, value):
        self._openTypeGaspRangeRecords = _convert_gasp_range_records(value)

    openTypeHeadCreated: Optional[str] = None
    openTypeHeadLowestRecPPEM: Optional[int] = attr.ib(
        default=None, validator=_optional_positive,
    )
    openTypeHeadFlags: Optional[List[int]] = None

    openTypeHheaAscender: Optional[int] = None
    openTypeHheaDescender: Optional[int] = None
    openTypeHheaLineGap: Optional[int] = None
    openTypeHheaCaretSlopeRise: Optional[int] = None
    openTypeHheaCaretSlopeRun: Optional[int] = None
    openTypeHheaCaretOffset: Optional[int] = None

    openTypeNameDesigner: Optional[str] = None
    openTypeNameDesignerURL: Optional[str] = None
    openTypeNameManufacturer: Optional[str] = None
    openTypeNameManufacturerURL: Optional[str] = None
    openTypeNameLicense: Optional[str] = None
    openTypeNameLicenseURL: Optional[str] = None
    openTypeNameVersion: Optional[str] = None
    openTypeNameUniqueID: Optional[str] = None
    openTypeNameDescription: Optional[str] = None
    openTypeNamePreferredFamilyName: Optional[str] = None
    openTypeNamePreferredSubfamilyName: Optional[str] = None
    openTypeNameCompatibleFullName: Optional[str] = None
    openTypeNameSampleText: Optional[str] = None
    openTypeNameWWSFamilyName: Optional[str] = None
    openTypeNameWWSSubfamilyName: Optional[str] = None

    _openTypeNameRecords: Optional[List[NameRecord]] = attr.ib(
        default=None, converter=_convert_name_records
    )

    @property
    def openTypeNameRecords(self):
        return self._openTypeNameRecords

    @openTypeNameRecords.setter
    def openTypeNameRecords(self, value):
        self._openTypeNameRecords = _convert_name_records(value)

    _openTypeOS2WidthClass: Optional[WidthClass] = attr.ib(
        default=None, converter=_convert_WidthClass
    )

    @property
    def openTypeOS2WidthClass(self):
        return self._openTypeOS2WidthClass

    @openTypeOS2WidthClass.setter
    def openTypeOS2WidthClass(self, value):
        self._openTypeOS2WidthClass = value if value is None else WidthClass(value)

    openTypeOS2WeightClass: Optional[int] = attr.ib(default=None)

    @openTypeOS2WeightClass.validator
    def _validate_weight_class(self, attribute, value):
        if value is not None and (value < 1 or value > 1000):
            raise ValueError("'openTypeOS2WeightClass' must be between 1 and 1000")

    openTypeOS2Selection: Optional[List[int]] = None
    openTypeOS2VendorID: Optional[str] = None
    openTypeOS2Panose: Optional[List[int]] = None
    openTypeOS2FamilyClass: Optional[List[int]] = None
    openTypeOS2UnicodeRanges: Optional[List[int]] = None
    openTypeOS2CodePageRanges: Optional[List[int]] = None
    openTypeOS2TypoAscender: Optional[int] = None
    openTypeOS2TypoDescender: Optional[int] = None
    openTypeOS2TypoLineGap: Optional[int] = None
    openTypeOS2WinAscent: Optional[int] = attr.ib(
        default=None, validator=_optional_positive
    )
    openTypeOS2WinDescent: Optional[int] = attr.ib(
        default=None, validator=_optional_positive
    )
    openTypeOS2Type: Optional[List[int]] = None
    openTypeOS2SubscriptXSize: Optional[int] = None
    openTypeOS2SubscriptYSize: Optional[int] = None
    openTypeOS2SubscriptXOffset: Optional[int] = None
    openTypeOS2SubscriptYOffset: Optional[int] = None
    openTypeOS2SuperscriptXSize: Optional[int] = None
    openTypeOS2SuperscriptYSize: Optional[int] = None
    openTypeOS2SuperscriptXOffset: Optional[int] = None
    openTypeOS2SuperscriptYOffset: Optional[int] = None
    openTypeOS2StrikeoutSize: Optional[int] = None
    openTypeOS2StrikeoutPosition: Optional[int] = None

    openTypeVheaVertTypoAscender: Optional[int] = None
    openTypeVheaVertTypoDescender: Optional[int] = None
    openTypeVheaVertTypoLineGap: Optional[int] = None
    openTypeVheaCaretSlopeRise: Optional[int] = None
    openTypeVheaCaretSlopeRun: Optional[int] = None
    openTypeVheaCaretOffset: Optional[int] = None

    postscriptFontName: Optional[str] = None
    postscriptFullName: Optional[str] = None
    postscriptSlantAngle: Optional[Number] = None
    postscriptUniqueID: Optional[int] = None
    postscriptUnderlineThickness: Optional[Number] = None
    postscriptUnderlinePosition: Optional[Number] = None
    postscriptIsFixedPitch: Optional[bool] = None
    postscriptBlueValues: Optional[List[Number]] = None
    postscriptOtherBlues: Optional[List[Number]] = None
    postscriptFamilyBlues: Optional[List[Number]] = None
    postscriptFamilyOtherBlues: Optional[List[Number]] = None
    postscriptStemSnapH: Optional[List[Number]] = None
    postscriptStemSnapV: Optional[List[Number]] = None
    postscriptBlueFuzz: Optional[Number] = None
    postscriptBlueShift: Optional[Number] = None
    postscriptBlueScale: Optional[float] = None
    postscriptForceBold: Optional[bool] = None
    postscriptDefaultWidthX: Optional[Number] = None
    postscriptNominalWidthX: Optional[Number] = None
    postscriptWeightName: Optional[str] = None
    postscriptDefaultCharacter: Optional[str] = None
    postscriptWindowsCharacterSet: Optional[str] = None

    # old stuff
    macintoshFONDName: Optional[str] = None
    macintoshFONDFamilyID: Optional[int] = None
    year: Optional[int] = None

    @classmethod
    def read(cls, reader):
        self = cls()
        reader.readInfo(self)
        return self
