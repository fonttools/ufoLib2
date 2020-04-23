from ufoLib2.objects import Glyph, Guideline


def test_font_mapping_behavior(ufo_UbuTestData):
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


def test_font_defcon_behavior(ufo_UbuTestData):
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
    assert font.info.guidelines[-1] is guideline

    font.newLayer("abc")
    assert "abc" in font.layers

    font.renameLayer("abc", "def")
    assert "abc" not in font.layers
    assert "def" in font.layers
