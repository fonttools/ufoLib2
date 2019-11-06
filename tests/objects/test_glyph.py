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

    def _assert_equal_but_distinct_objects(glyph1, glyph2):
        assert glyph1.width == glyph2.width
        assert glyph1.height == glyph2.height
        assert glyph1.unicodes == glyph2.unicodes
        assert glyph1.unicodes is not glyph2.unicodes
        assert glyph1.image == glyph2.image
        assert glyph1.image is not glyph2.image
        assert glyph1.note == glyph2.note
        assert glyph1.lib == glyph2.lib
        assert glyph1.lib is not glyph2.lib
        assert glyph1.lib["bar"] == glyph2.lib["bar"]
        assert glyph1.lib["bar"] is not glyph2.lib["bar"]
        assert glyph1.anchors == glyph2.anchors
        assert glyph1.anchors is not glyph2.anchors
        assert glyph1.anchors[0] is not glyph2.anchors[0]
        assert glyph1.guidelines == glyph2.guidelines
        assert glyph1.guidelines is not glyph2.guidelines
        assert glyph1.guidelines[0] is not glyph2.guidelines[0]
        assert glyph1.contours == glyph2.contours
        assert glyph1.contours is not glyph2.contours
        assert glyph1.contours[0] is not glyph2.contours[0]
        assert glyph1.components == glyph2.components
        assert glyph1.components is not glyph2.components
        assert glyph1.components[0] is not glyph2.components[0]

    b.copyDataFromGlyph(a)
    assert b.name != a.name
    _assert_equal_but_distinct_objects(b, a)

    c = a.copy()
    assert c.name == a.name
    _assert_equal_but_distinct_objects(c, a)

    d = a.copy(name="d")
    assert d.name == "d"
    _assert_equal_but_distinct_objects(d, a)
