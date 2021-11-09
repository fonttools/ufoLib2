from __future__ import annotations

from pathlib import Path

from ufoLib2.objects import Font, Glyph, Guideline


def test_font_equality(datadir: Path) -> None:
    font1 = Font.open(datadir / "UbuTestData.ufo")
    font2 = Font.open(datadir / "UbuTestData.ufo")

    assert font1 == font2

    class SubFont(Font):
        pass

    font3 = SubFont.open(datadir / "UbuTestData.ufo")
    assert font1 != font3


def test_font_mapping_behavior(ufo_UbuTestData: Font) -> None:
    font = ufo_UbuTestData

    assert font["a"] is font.layers.defaultLayer["a"]
    assert ("a" in font) == ("a" in font.layers.defaultLayer)
    assert len(font) == len(font.layers.defaultLayer)

    glyph = Glyph("b")
    font["b"] = glyph
    assert font["b"] is glyph
    assert font.layers.defaultLayer["b"] is glyph

    del font["a"]
    assert "a" not in font
    assert "a" not in font.layers.defaultLayer


def test_font_defcon_behavior(ufo_UbuTestData: Font) -> None:
    font = ufo_UbuTestData

    font.newGlyph("b")
    assert "b" in font

    glyph = Glyph("c")
    font.addGlyph(glyph)
    assert font["c"] is glyph

    font.renameGlyph("c", "d")
    assert font["d"] is glyph
    assert font["d"].name == "d"

    guideline = Guideline(x=1)
    font.appendGuideline(guideline)
    assert font.info.guidelines is not None
    assert font.info.guidelines[-1] is guideline

    font.appendGuideline({"y": 1, "name": "asdf"})
    assert font.info.guidelines[-1].name == "asdf"

    font.newLayer("abc")
    assert "abc" in font.layers

    font.renameLayer("abc", "def")
    assert "abc" not in font.layers
    assert "def" in font.layers


def test_nondefault_layer_name(ufo_UbuTestData: Font, tmp_path: Path) -> None:
    font = ufo_UbuTestData

    font.layers.renameLayer("public.default", "abc")
    font.save(tmp_path / "abc.ufo")
    font2 = Font.open(tmp_path / "abc.ufo")

    assert font2.layers.defaultLayer.name == "abc"
    assert font2.layers.defaultLayer is font2.layers["abc"]


def test_layer_order(ufo_UbuTestData: Font) -> None:
    font = ufo_UbuTestData

    assert font.layers.layerOrder == ["public.default", "public.background"]
    font.layers.layerOrder = ["public.background", "public.default"]
    assert font.layers.layerOrder == ["public.background", "public.default"]


def test_bounds(ufo_UbuTestData: Font) -> None:
    font = ufo_UbuTestData

    assert font.bounds == (8, -11, 655, 693)
    assert font.controlPointBounds == (8, -11, 655, 693)


def test_data_images_init() -> None:
    font = Font(
        data={"aaa": b"123", "bbb/c": b"456"},
        images={"a.png": b"\x89PNG\r\n\x1a\n", "b.png": b"\x89PNG\r\n\x1a\n"},
    )

    assert font.data["aaa"] == b"123"
    assert font.data["bbb/c"] == b"456"
    assert font.images["a.png"] == b"\x89PNG\r\n\x1a\n"
    assert font.images["b.png"] == b"\x89PNG\r\n\x1a\n"
