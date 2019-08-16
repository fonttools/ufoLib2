import attr
from enum import IntEnum
from typing import Optional, List, Union
from ufoLib2.objects.misc import AttrDictMixin
from ufoLib2.objects.guideline import Guideline


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
    SYMMETRIC_SMOOTHING = 2
    SYMMETRIC_GRIDFIT = 3


def _convert_GaspBehavior(seq) -> List[GaspBehavior]:
    return [v if isinstance(v, GaspBehavior) else GaspBehavior(v) for v in seq]


@attr.s(slots=True)
class GaspRangeRecord(AttrDictMixin):
    rangeMaxPPEM = attr.ib(validator=_positive, type=int)
    rangeGaspBehavior = attr.ib(
        converter=_convert_GaspBehavior,
        type=List[GaspBehavior],  # use Set instead of List?
    )


@attr.s(slots=True)
class NameRecord(AttrDictMixin):
    nameID = attr.ib(validator=_positive, type=int)
    platformID = attr.ib(validator=_positive, type=int)
    encodingID = attr.ib(validator=_positive, type=int)
    languageID = attr.ib(validator=_positive, type=int)
    string = attr.ib(type=str)


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
        return
    result = []
    for d in lst:
        if isinstance(d, klass):
            result.append(d)
        else:
            result.append(klass(**d))
    return result


def _convert_guidelines(values) -> Optional[List[Guideline]]:
    return _convert_optional_list(values, Guideline)


def _convert_gasp_range_records(values) -> Optional[List[GaspRangeRecord]]:
    return _convert_optional_list(values, GaspRangeRecord)


def _convert_name_records(values) -> Optional[List[NameRecord]]:
    return _convert_optional_list(values, NameRecord)


def _convert_WidthClass(value) -> Optional[WidthClass]:
    return value if value is None else WidthClass(value)


@attr.s(slots=True)
class Info(object):
    familyName = attr.ib(default=None, type=Optional[str])
    styleName = attr.ib(default=None, type=Optional[str])
    styleMapFamilyName = attr.ib(default=None, type=Optional[str])
    styleMapStyleName = attr.ib(default=None, type=Optional[str])
    versionMajor = attr.ib(
        default=None, validator=_optional_positive, type=Optional[int]
    )
    versionMinor = attr.ib(
        default=None, validator=_optional_positive, type=Optional[int]
    )

    copyright = attr.ib(default=None, type=Optional[str])
    trademark = attr.ib(default=None, type=Optional[str])

    unitsPerEm = attr.ib(
        default=None, validator=_optional_positive, type=Optional[Union[float, int]]
    )
    descender = attr.ib(default=None, type=Optional[Union[float, int]])
    xHeight = attr.ib(default=None, type=Optional[Union[float, int]])
    capHeight = attr.ib(default=None, type=Optional[Union[float, int]])
    ascender = attr.ib(default=None, type=Optional[Union[float, int]])
    italicAngle = attr.ib(default=None, type=Optional[Union[float, int]])

    note = attr.ib(default=None, type=Optional[str])

    _guidelines = attr.ib(
        default=None, converter=_convert_guidelines, type=Optional[List[Guideline]]
    )

    @property
    def guidelines(self):
        return self._guidelines

    @guidelines.setter
    def guidelines(self, value):
        self._guidelines = _convert_guidelines(value)

    _openTypeGaspRangeRecords = attr.ib(
        default=None,
        converter=_convert_gasp_range_records,
        type=Optional[List[GaspRangeRecord]],
    )

    @property
    def openTypeGaspRangeRecords(self):
        return self._openTypeGaspRangeRecords

    @openTypeGaspRangeRecords.setter
    def openTypeGaspRangeRecords(self, value):
        self._openTypeGaspRangeRecords = _convert_gasp_range_records(value)

    openTypeHeadCreated = attr.ib(default=None, type=Optional[str])
    openTypeHeadLowestRecPPEM = attr.ib(
        default=None, validator=_optional_positive, type=Optional[int]
    )
    openTypeHeadFlags = attr.ib(default=None, type=Optional[List[int]])

    openTypeHheaAscender = attr.ib(default=None, type=Optional[int])
    openTypeHheaDescender = attr.ib(default=None, type=Optional[int])
    openTypeHheaLineGap = attr.ib(default=None, type=Optional[int])
    openTypeHheaCaretSlopeRise = attr.ib(default=None, type=Optional[int])
    openTypeHheaCaretSlopeRun = attr.ib(default=None, type=Optional[int])
    openTypeHheaCaretOffset = attr.ib(default=None, type=Optional[int])

    openTypeNameDesigner = attr.ib(default=None, type=Optional[str])
    openTypeNameDesignerURL = attr.ib(default=None, type=Optional[str])
    openTypeNameManufacturer = attr.ib(default=None, type=Optional[str])
    openTypeNameManufacturerURL = attr.ib(default=None, type=Optional[str])
    openTypeNameLicense = attr.ib(default=None, type=Optional[str])
    openTypeNameLicenseURL = attr.ib(default=None, type=Optional[str])
    openTypeNameVersion = attr.ib(default=None, type=Optional[str])
    openTypeNameUniqueID = attr.ib(default=None, type=Optional[str])
    openTypeNameDescription = attr.ib(default=None, type=Optional[str])
    openTypeNamePreferredFamilyName = attr.ib(default=None, type=Optional[str])
    openTypeNamePreferredSubfamilyName = attr.ib(default=None, type=Optional[str])
    openTypeNameCompatibleFullName = attr.ib(default=None, type=Optional[str])
    openTypeNameSampleText = attr.ib(default=None, type=Optional[str])
    openTypeNameWWSFamilyName = attr.ib(default=None, type=Optional[str])
    openTypeNameWWSSubfamilyName = attr.ib(default=None, type=Optional[str])

    _openTypeNameRecords = attr.ib(
        default=None, converter=_convert_name_records, type=Optional[List[NameRecord]]
    )

    @property
    def openTypeNameRecords(self):
        return self._openTypeNameRecords

    @openTypeNameRecords.setter
    def openTypeNameRecords(self, value):
        self._openTypeNameRecords = _convert_name_records(value)

    _openTypeOS2WidthClass = attr.ib(
        default=None, converter=_convert_WidthClass, type=Optional[WidthClass]
    )

    @property
    def openTypeOS2WidthClass(self):
        return self._openTypeOS2WidthClass

    @openTypeOS2WidthClass.setter
    def openTypeOS2WidthClass(self, value):
        self._openTypeOS2WidthClass = value if value is None else WidthClass(value)

    openTypeOS2WeightClass = attr.ib(default=None, type=Optional[int])

    @openTypeOS2WeightClass.validator
    def _validate_weight_class(self, attribute, value):
        if value is not None and (value < 1 or value > 1000):
            raise ValueError("'openTypeOS2WeightClass' must be between 1 and 1000")

    openTypeOS2Selection = attr.ib(default=None, type=Optional[List[int]])
    openTypeOS2VendorID = attr.ib(default=None, type=Optional[str])
    openTypeOS2Panose = attr.ib(default=None, type=Optional[List[int]])
    openTypeOS2FamilyClass = attr.ib(default=None, type=Optional[List[int]])
    openTypeOS2UnicodeRanges = attr.ib(default=None, type=Optional[List[int]])
    openTypeOS2CodePageRanges = attr.ib(default=None, type=Optional[List[int]])
    openTypeOS2TypoAscender = attr.ib(default=None, type=Optional[int])
    openTypeOS2TypoDescender = attr.ib(default=None, type=Optional[int])
    openTypeOS2TypoLineGap = attr.ib(default=None, type=Optional[int])
    openTypeOS2WinAscent = attr.ib(
        default=None, validator=_optional_positive, type=Optional[int]
    )
    openTypeOS2WinDescent = attr.ib(
        default=None, validator=_optional_positive, type=Optional[int]
    )
    openTypeOS2Type = attr.ib(default=None, type=Optional[List[int]])
    openTypeOS2SubscriptXSize = attr.ib(default=None, type=Optional[int])
    openTypeOS2SubscriptYSize = attr.ib(default=None, type=Optional[int])
    openTypeOS2SubscriptXOffset = attr.ib(default=None, type=Optional[int])
    openTypeOS2SubscriptYOffset = attr.ib(default=None, type=Optional[int])
    openTypeOS2SuperscriptXSize = attr.ib(default=None, type=Optional[int])
    openTypeOS2SuperscriptYSize = attr.ib(default=None, type=Optional[int])
    openTypeOS2SuperscriptXOffset = attr.ib(default=None, type=Optional[int])
    openTypeOS2SuperscriptYOffset = attr.ib(default=None, type=Optional[int])
    openTypeOS2StrikeoutSize = attr.ib(default=None, type=Optional[int])
    openTypeOS2StrikeoutPosition = attr.ib(default=None, type=Optional[int])

    openTypeVheaVertTypoAscender = attr.ib(default=None, type=Optional[int])
    openTypeVheaVertTypoDescender = attr.ib(default=None, type=Optional[int])
    openTypeVheaVertTypoLineGap = attr.ib(default=None, type=Optional[int])
    openTypeVheaCaretSlopeRise = attr.ib(default=None, type=Optional[int])
    openTypeVheaCaretSlopeRun = attr.ib(default=None, type=Optional[int])
    openTypeVheaCaretOffset = attr.ib(default=None, type=Optional[int])

    postscriptFontName = attr.ib(default=None, type=Optional[str])
    postscriptFullName = attr.ib(default=None, type=Optional[str])
    postscriptSlantAngle = attr.ib(default=None, type=Optional[Union[float, int]])
    postscriptUniqueID = attr.ib(default=None, type=Optional[int])
    postscriptUnderlineThickness = attr.ib(
        default=None, type=Optional[Union[float, int]]
    )
    postscriptUnderlinePosition = attr.ib(
        default=None, type=Optional[Union[float, int]]
    )
    postscriptIsFixedPitch = attr.ib(default=None, type=Optional[bool])
    postscriptBlueValues = attr.ib(default=None, type=Optional[List[Union[float, int]]])
    postscriptOtherBlues = attr.ib(default=None, type=Optional[List[Union[float, int]]])
    postscriptFamilyBlues = attr.ib(
        default=None, type=Optional[List[Union[float, int]]]
    )
    postscriptFamilyOtherBlues = attr.ib(
        default=None, type=Optional[List[Union[float, int]]]
    )
    postscriptStemSnapH = attr.ib(default=None, type=Optional[List[Union[float, int]]])
    postscriptStemSnapV = attr.ib(default=None, type=Optional[List[Union[float, int]]])
    postscriptBlueFuzz = attr.ib(default=None, type=Optional[Union[float, int]])
    postscriptBlueShift = attr.ib(default=None, type=Optional[Union[float, int]])
    postscriptBlueScale = attr.ib(default=None, type=Optional[float])
    postscriptForceBold = attr.ib(default=None, type=Optional[bool])
    postscriptDefaultWidthX = attr.ib(default=None, type=Optional[Union[float, int]])
    postscriptNominalWidthX = attr.ib(default=None, type=Optional[Union[float, int]])
    postscriptWeightName = attr.ib(default=None, type=Optional[str])
    postscriptDefaultCharacter = attr.ib(default=None, type=Optional[str])
    postscriptWindowsCharacterSet = attr.ib(default=None, type=Optional[str])

    # old stuff
    macintoshFONDName = attr.ib(default=None, type=Optional[str])
    macintoshFONDFamilyID = attr.ib(default=None, type=Optional[int])
    year = attr.ib(default=None, type=Optional[int])
