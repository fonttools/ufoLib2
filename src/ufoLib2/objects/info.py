import attr
from enum import IntEnum
from functools import partial
from ufoLib2.types import (
    Optional,
    List,
    Text,
    Integer,
    OptText,
    OptInteger,
    OptFloat,
    OptNumber,
    OptBool,
    OptIntList,
    OptNumList,
)
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


@attr.s(slots=True)
class GaspRangeRecord(AttrDictMixin):
    rangeMaxPPEM = attr.ib(validator=_positive, type=Integer)
    rangeGaspBehavior = attr.ib(
        converter=lambda seq: [
            v if isinstance(v, GaspBehavior) else GaspBehavior(v) for v in seq
        ],
        type=List[GaspBehavior],  # use Set instead of List?
    )


@attr.s(slots=True)
class NameRecord(AttrDictMixin):
    nameID = attr.ib(validator=_positive, type=Integer)
    platformID = attr.ib(validator=_positive, type=Integer)
    encodingID = attr.ib(validator=_positive, type=Integer)
    languageID = attr.ib(validator=_positive, type=Integer)
    string = attr.ib(type=Text)


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


_convert_guidelines = partial(_convert_optional_list, klass=Guideline)
_convert_gasp_range_records = partial(
    _convert_optional_list, klass=GaspRangeRecord
)
_convert_name_records = partial(_convert_optional_list, klass=NameRecord)


@attr.s(slots=True)
class Info(object):
    familyName = attr.ib(default=None, type=OptText)
    styleName = attr.ib(default=None, type=OptText)
    styleMapFamilyName = attr.ib(default=None, type=OptText)
    styleMapStyleName = attr.ib(default=None, type=OptText)
    versionMajor = attr.ib(
        default=None, validator=_optional_positive, type=OptInteger
    )
    versionMinor = attr.ib(
        default=None, validator=_optional_positive, type=OptInteger
    )

    copyright = attr.ib(default=None, type=OptText)
    trademark = attr.ib(default=None, type=OptText)

    unitsPerEm = attr.ib(
        default=None, validator=_optional_positive, type=OptNumber
    )
    descender = attr.ib(default=None, type=OptNumber)
    xHeight = attr.ib(default=None, type=OptNumber)
    capHeight = attr.ib(default=None, type=OptNumber)
    ascender = attr.ib(default=None, type=OptNumber)
    italicAngle = attr.ib(default=None, type=OptNumber)

    note = attr.ib(default=None, type=OptText)

    _guidelines = attr.ib(
        default=None,
        converter=_convert_guidelines,
        type=Optional[List[Guideline]],
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

    openTypeHeadCreated = attr.ib(default=None, type=OptText)
    openTypeHeadLowestRecPPEM = attr.ib(
        default=None, validator=_optional_positive, type=OptInteger
    )
    openTypeHeadFlags = attr.ib(default=None, type=OptIntList)

    openTypeHheaAscender = attr.ib(default=None, type=OptInteger)
    openTypeHheaDescender = attr.ib(default=None, type=OptInteger)
    openTypeHheaLineGap = attr.ib(default=None, type=OptInteger)
    openTypeHheaCaretSlopeRise = attr.ib(default=None, type=OptInteger)
    openTypeHheaCaretSlopeRun = attr.ib(default=None, type=OptInteger)
    openTypeHheaCaretOffset = attr.ib(default=None, type=OptInteger)

    openTypeNameDesigner = attr.ib(default=None, type=OptText)
    openTypeNameDesignerURL = attr.ib(default=None, type=OptText)
    openTypeNameManufacturer = attr.ib(default=None, type=OptText)
    openTypeNameManufacturerURL = attr.ib(default=None, type=OptText)
    openTypeNameLicense = attr.ib(default=None, type=OptText)
    openTypeNameLicenseURL = attr.ib(default=None, type=OptText)
    openTypeNameVersion = attr.ib(default=None, type=OptText)
    openTypeNameUniqueID = attr.ib(default=None, type=OptText)
    openTypeNameDescription = attr.ib(default=None, type=OptText)
    openTypeNamePreferredFamilyName = attr.ib(default=None, type=OptText)
    openTypeNamePreferredSubfamilyName = attr.ib(default=None, type=OptText)
    openTypeNameCompatibleFullName = attr.ib(default=None, type=OptText)
    openTypeNameSampleText = attr.ib(default=None, type=OptText)
    openTypeNameWWSFamilyName = attr.ib(default=None, type=OptText)
    openTypeNameWWSSubfamilyName = attr.ib(default=None, type=OptText)

    _openTypeNameRecords = attr.ib(
        default=None,
        converter=_convert_name_records,
        type=Optional[List[NameRecord]],
    )

    @property
    def openTypeNameRecords(self):
        return self._openTypeNameRecords

    @openTypeNameRecords.setter
    def openTypeNameRecords(self, value):
        self._openTypeNameRecords = _convert_name_records(value)

    _openTypeOS2WidthClass = attr.ib(
        default=None,
        converter=lambda v: v if v is None else WidthClass(v),
        type=Optional[WidthClass],
    )

    @property
    def openTypeOS2WidthClass(self):
        return self._openTypeOS2WidthClass

    @openTypeOS2WidthClass.setter
    def openTypeOS2WidthClass(self, value):
        self._openTypeOS2WidthClass = (
            value if value is None else WidthClass(value)
        )

    openTypeOS2WeightClass = attr.ib(default=None, type=OptInteger)

    @openTypeOS2WeightClass.validator
    def _validate_weight_class(self, attribute, value):
        if value is not None and (value < 1 or value > 1000):
            raise ValueError(
                "'openTypeOS2WeightClass' must be between 1 and 1000"
            )

    openTypeOS2Selection = attr.ib(default=None, type=OptIntList)
    openTypeOS2VendorID = attr.ib(default=None, type=OptText)
    openTypeOS2Panose = attr.ib(default=None, type=OptIntList)
    openTypeOS2FamilyClass = attr.ib(default=None, type=OptIntList)
    openTypeOS2UnicodeRanges = attr.ib(default=None, type=OptIntList)
    openTypeOS2CodePageRanges = attr.ib(default=None, type=OptIntList)
    openTypeOS2TypoAscender = attr.ib(default=None, type=OptInteger)
    openTypeOS2TypoDescender = attr.ib(default=None, type=OptInteger)
    openTypeOS2TypoLineGap = attr.ib(default=None, type=OptInteger)
    openTypeOS2WinAscent = attr.ib(
        default=None, validator=_optional_positive, type=OptInteger
    )
    openTypeOS2WinDescent = attr.ib(
        default=None, validator=_optional_positive, type=OptInteger
    )
    openTypeOS2Type = attr.ib(default=None, type=OptIntList)
    openTypeOS2SubscriptXSize = attr.ib(default=None, type=OptInteger)
    openTypeOS2SubscriptYSize = attr.ib(default=None, type=OptInteger)
    openTypeOS2SubscriptXOffset = attr.ib(default=None, type=OptInteger)
    openTypeOS2SubscriptYOffset = attr.ib(default=None, type=OptInteger)
    openTypeOS2SuperscriptXSize = attr.ib(default=None, type=OptInteger)
    openTypeOS2SuperscriptYSize = attr.ib(default=None, type=OptInteger)
    openTypeOS2SuperscriptXOffset = attr.ib(default=None, type=OptInteger)
    openTypeOS2SuperscriptYOffset = attr.ib(default=None, type=OptInteger)
    openTypeOS2StrikeoutSize = attr.ib(default=None, type=OptInteger)
    openTypeOS2StrikeoutPosition = attr.ib(default=None, type=OptInteger)

    openTypeVheaVertTypoAscender = attr.ib(default=None, type=OptInteger)
    openTypeVheaVertTypoDescender = attr.ib(default=None, type=OptInteger)
    openTypeVheaVertTypoLineGap = attr.ib(default=None, type=OptInteger)
    openTypeVheaCaretSlopeRise = attr.ib(default=None, type=OptInteger)
    openTypeVheaCaretSlopeRun = attr.ib(default=None, type=OptInteger)
    openTypeVheaCaretOffset = attr.ib(default=None, type=OptInteger)

    postscriptFontName = attr.ib(default=None, type=OptText)
    postscriptFullName = attr.ib(default=None, type=OptText)
    postscriptSlantAngle = attr.ib(default=None, type=OptNumber)
    postscriptUniqueID = attr.ib(default=None, type=OptInteger)
    postscriptUnderlineThickness = attr.ib(default=None, type=OptNumber)
    postscriptUnderlinePosition = attr.ib(default=None, type=OptNumber)
    postscriptIsFixedPitch = attr.ib(default=None, type=OptBool)
    postscriptBlueValues = attr.ib(default=None, type=OptNumList)
    postscriptOtherBlues = attr.ib(default=None, type=OptNumList)
    postscriptFamilyBlues = attr.ib(default=None, type=OptNumList)
    postscriptFamilyOtherBlues = attr.ib(default=None, type=OptNumList)
    postscriptStemSnapH = attr.ib(default=None, type=OptNumList)
    postscriptStemSnapV = attr.ib(default=None, type=OptNumList)
    postscriptBlueFuzz = attr.ib(default=None, type=OptNumber)
    postscriptBlueShift = attr.ib(default=None, type=OptNumber)
    postscriptBlueScale = attr.ib(default=None, type=OptFloat)
    postscriptForceBold = attr.ib(default=None, type=OptBool)
    postscriptDefaultWidthX = attr.ib(default=None, type=OptNumber)
    postscriptNominalWidthX = attr.ib(default=None, type=OptNumber)
    postscriptWeightName = attr.ib(default=None, type=OptText)
    postscriptDefaultCharacter = attr.ib(default=None, type=OptText)
    postscriptWindowsCharacterSet = attr.ib(default=None, type=OptText)

    # old stuff
    macintoshFONDName = attr.ib(default=None, type=OptText)
    macintoshFONDFamilyID = attr.ib(default=None, type=OptInteger)
    year = attr.ib(default=None, type=OptInteger)
