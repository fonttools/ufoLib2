from __future__ import annotations

from typing import Any

import pytest
from fontTools.misc.transform import Transform

from ufoLib2.constants import DATA_LIB_KEY
from ufoLib2.converters import json_converter
from ufoLib2.objects import (
    Anchor,
    Component,
    Contour,
    DataSet,
    Font,
    Glyph,
    Guideline,
    Image,
    ImageSet,
    Info,
    Kerning,
    Layer,
    LayerSet,
    Lib,
    Point,
)
from ufoLib2.objects.info import GaspBehavior, GaspRangeRecord, NameRecord, WidthClass


@pytest.mark.parametrize(
    "obj, expected",
    [
        (Anchor(0, 0), {"x": 0, "y": 0}),
        (
            Anchor(1, -2, "top", "1,0,0,1", "01234"),
            {"x": 1, "y": -2, "name": "top", "color": "1,0,0,1", "identifier": "01234"},
        ),
        (Point(0, 0), {"x": 0, "y": 0}),
        (
            Point(1.5, -2.1, "qcurve", True, "foobar", "12345"),
            {
                "x": 1.5,
                "y": -2.1,
                "type": "qcurve",
                "smooth": True,
                "name": "foobar",
                "identifier": "12345",
            },
        ),
        (Component("a"), {"baseGlyph": "a"}),
        (
            Component("b", Transform(1, 0, 0, 0.5, 10, 20), "abcd1234"),
            {
                "baseGlyph": "b",
                "transformation": (1, 0, 0, 0.5, 10, 20),
                "identifier": "abcd1234",
            },
        ),
        (Contour(), {}),
        (
            Contour([Point(0, 0), Point(1, 2)], "zzzz"),
            {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 2}], "identifier": "zzzz"},
        ),
        (Image(), {}),
        (
            Image("path/to/image.png", Transform(2, 0, 0, 2, 0, 0), "1,1,1,1"),
            {
                "fileName": "path/to/image.png",
                "transformation": (2, 0, 0, 2, 0, 0),
                "color": "1,1,1,1",
            },
        ),
        (Lib(), {}),
        (Lib(foo="bar"), {"foo": "bar"}),
        (Lib(foo=[1, 2], bar={"baz": 3}), {"foo": [1, 2], "bar": {"baz": 3}}),
        (
            Lib(foo={"bar": b"baz"}, oof=[b"rab", "zab"]),
            {
                "foo": {
                    "bar": {"data": "YmF6", "type": DATA_LIB_KEY},
                },
                "oof": [
                    {"data": "cmFi", "type": DATA_LIB_KEY},
                    "zab",
                ],
            },
        ),
        (Guideline(x=0, name="foo"), {"x": 0, "name": "foo"}),
        (Guideline(y=1, name="bar"), {"y": 1, "name": "bar"}),
        (
            Guideline(
                x=1, y=2, angle=45.0, name="baz", color="0,1,0.5,1", identifier="0001"
            ),
            {
                "x": 1,
                "y": 2,
                "angle": 45.0,
                "name": "baz",
                "color": "0,1,0.5,1",
                "identifier": "0001",
            },
        ),
        (Glyph(), {}),
        (
            Glyph(
                "a",
                width=1000,
                height=800,
                unicodes=[97],
                lib=Lib(foo=b"bar"),
                note="Latin lowercase 'a'",
                anchors=[Anchor(100, 200, "top"), Anchor(100, -50, "bottom")],
                contours=[
                    Contour(
                        [Point(0, 0, "line"), Point(1, 1, "line"), Point(1, 0, "line")]
                    ),
                    Contour(
                        [
                            Point(2, 2, "move"),
                            Point(3, 2),
                            Point(4, 1),
                            Point(4, -1, "curve"),
                        ]
                    ),
                ],
                guidelines=[Guideline(x=10)],
            ),
            {
                "name": "a",
                "width": 1000,
                "height": 800,
                "unicodes": [97],
                "lib": {"foo": {"data": "YmFy", "type": DATA_LIB_KEY}},
                "note": "Latin lowercase 'a'",
                "anchors": [
                    {"name": "top", "x": 100, "y": 200},
                    {"name": "bottom", "x": 100, "y": -50},
                ],
                "contours": [
                    {
                        "points": [
                            {"x": 0, "y": 0, "type": "line"},
                            {"x": 1, "y": 1, "type": "line"},
                            {"x": 1, "y": 0, "type": "line"},
                        ]
                    },
                    {
                        "points": [
                            {"x": 2, "y": 2, "type": "move"},
                            {"x": 3, "y": 2},
                            {"x": 4, "y": 1},
                            {"x": 4, "y": -1, "type": "curve"},
                        ]
                    },
                ],
                "guidelines": [{"x": 10}],
            },
        ),
        (Kerning(), {}),
        (
            Kerning({("a", "b"): -10, ("a", "d"): 5, ("b", "d"): 0}),
            {"a": {"b": -10, "d": 5}, "b": {"d": 0}},
        ),
        (
            Info(
                familyName="Test",
                styleName="Bold",
                versionMajor=2,
                versionMinor=1,
                unitsPerEm=1000,
                guidelines=[Guideline(y=500, name="x-height")],
                openTypeGaspRangeRecords=[
                    GaspRangeRecord(
                        rangeMaxPPEM=18,
                        rangeGaspBehavior=[GaspBehavior.SYMMETRIC_SMOOTHING],
                    )
                ],
                openTypeHeadFlags=[0, 1, 2],
                openTypeNameRecords=[
                    NameRecord(
                        nameID=5,
                        platformID=0,
                        encodingID=0,
                        languageID=0,
                        string="Version 2.1",
                    )
                ],
                openTypeOS2WidthClass=WidthClass.MEDIUM,
                postscriptBlueScale=0.25,
            ),
            {
                "familyName": "Test",
                "styleName": "Bold",
                "versionMajor": 2,
                "versionMinor": 1,
                "unitsPerEm": 1000,
                "guidelines": [{"y": 500, "name": "x-height"}],
                "openTypeGaspRangeRecords": [
                    {"rangeMaxPPEM": 18, "rangeGaspBehavior": [3]},
                ],
                "openTypeHeadFlags": [0, 1, 2],
                "openTypeNameRecords": [
                    {
                        "nameID": 5,
                        "platformID": 0,
                        "encodingID": 0,
                        "languageID": 0,
                        "string": "Version 2.1",
                    }
                ],
                "openTypeOS2WidthClass": 5,
                "postscriptBlueScale": 0.25,
            },
        ),
        (Layer(), {"name": "public.default"}),
        (
            Layer(
                name="foreground",
                glyphs={"a": Glyph("a"), "b": Glyph("b")},
                color="1,0,1,1",
                lib=Lib(foobar=0.1),
            ),
            {
                "name": "foreground",
                "glyphs": [{"name": "a"}, {"name": "b"}],
                "color": "1,0,1,1",
                "lib": {"foobar": 0.1},
            },
        ),
        (LayerSet.default(), {"layers": [{"name": "public.default"}]}),
        (
            LayerSet.from_iterable(
                [Layer("foreground"), Layer("background")],
                defaultLayerName="foreground",
            ),
            {
                "layers": [{"name": "foreground"}, {"name": "background"}],
                "defaultLayerName": "foreground",
            },
        ),
        (DataSet(), {}),
        (DataSet({"foo": b"bar"}), {"foo": "YmFy"}),
        (ImageSet(), {}),
        (ImageSet({"foo": b"bar"}), {"foo": "YmFy"}),
        (Font(), {"layers": [{"name": "public.default"}]}),
        (
            Font(
                layers=LayerSet.from_iterable(
                    [Layer(name="foreground"), Layer(name="background")],
                    defaultLayerName="foreground",
                )
            ),
            {
                "layers": [{"name": "foreground"}, {"name": "background"}],
                "defaultLayerName": "foreground",
            },
        ),
        (
            Font(
                layers=LayerSet.from_iterable([Layer(glyphs=[Glyph("a")])]),
                info=Info(familyName="Test"),
                features="languagesystem DFLT dflt;",
                groups={"LOWERCASE": ["a"]},
                kerning={("a", "a"): 10},
                lib={"foo": "bar"},
                data={"baz": b"\0"},
                images={"foobarbaz": b"\0"},
            ),
            {
                "layers": [{"name": "public.default", "glyphs": [{"name": "a"}]}],
                "info": {"familyName": "Test"},
                "features": "languagesystem DFLT dflt;",
                "groups": {"LOWERCASE": ["a"]},
                "kerning": {"a": {"a": 10}},
                "lib": {"foo": "bar"},
                "data": {"baz": "AA=="},
                "images": {"foobarbaz": "AA=="},
            },
        ),
    ],
)
def test_unstructure_structure(obj: Any, expected: dict[str, Any]) -> None:
    assert json_converter.unstructure(obj) == expected
    assert json_converter.structure(expected, type(obj)) == obj


def test_unstructure_lazy_font(ufo_UbuTestData):
    font1 = ufo_UbuTestData
    assert font1._lazy

    font_data = json_converter.unstructure(font1)
    assert not font1._lazy

    font2 = json_converter.structure(font_data, Font)
    assert font2 == font1
