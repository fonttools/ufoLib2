from ufoLib2.objects import Anchor, Component, Glyph, Guideline, Image


def test_copyDataFromGlyph(ufo_UbuTestData):
    font = ufo_UbuTestData

    a = font["a"]
    a.height = 500
    a.image = Image("a.png")
    a.note = "a note"
    a.lib = {"bar": [3, 2, 1]}
    a.anchors = [Anchor(250, 0, "bottom")]
    a.guidelines = [Guideline(y=500)]
    a.components = [Component("A")]

    b = Glyph("b")
    b.width = 350
    b.height = 1000
    b.image = Image("b.png")
    b.note = "b note"
    b.lib = {"foo": [1, 2, 3]}
    b.anchors = [Anchor(350, 800, "top")]
    b.guidelines = [Guideline(x=50)]

    assert b.name != a.name
    assert b.width != a.width
    assert b.height != a.height
    assert b.unicodes != a.unicodes
    assert b.image != a.image
    assert b.note != a.note
    assert b.lib != a.lib
    assert b.anchors != a.anchors
    assert b.guidelines != a.guidelines
    assert b.contours != a.contours
    assert b.components != a.components

    b.copyDataFromGlyph(a)

    assert b.name != a.name
    assert b.width == a.width
    assert b.height == a.height
    assert b.unicodes == a.unicodes
    assert b.image == a.image
    assert b.note == a.note
    assert b.lib == a.lib
    assert b.anchors == a.anchors
    assert b.guidelines == a.guidelines
    assert b.contours == a.contours
    assert b.components == a.components

    c = a.copy()
    assert c.name == a.name
    assert c.width == a.width
    assert c.height == a.height
    assert c.unicodes == a.unicodes
    assert c.image == a.image
    assert c.note == a.note
    assert c.lib == a.lib
    assert c.anchors == a.anchors
    assert c.guidelines == a.guidelines
    assert c.contours == a.contours
    assert c.components == a.components

    d = a.copy(name="d")
    assert d.name == "d"
    assert d.width == a.width
    assert d.height == a.height
    assert d.unicodes == a.unicodes
    assert d.image == a.image
    assert d.note == a.note
    assert d.lib == a.lib
    assert d.anchors == a.anchors
    assert d.guidelines == a.guidelines
    assert d.contours == a.contours
    assert d.components == a.components
