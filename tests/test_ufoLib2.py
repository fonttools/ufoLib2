from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Type

import pytest
from fontTools import ufoLib

import ufoLib2
import ufoLib2.objects
from ufoLib2.objects import Features, Font, Glyph, Kerning, Layer, LayerSet, Lib
from ufoLib2.objects.layerSet import _LAYER_NOT_LOADED
from ufoLib2.objects.misc import _DATA_NOT_LOADED


def test_import_version() -> None:
    assert hasattr(ufoLib2, "__version__")
    assert isinstance(ufoLib2.__version__, str)  # type: ignore


def test_LayerSet_load_layers_on_iteration(tmp_path: Path) -> None:
    ufo = ufoLib2.Font()
    ufo.layers.newLayer("test")
    ufo_save_path = tmp_path / "test.ufo"
    ufo.save(ufo_save_path)
    ufo = ufoLib2.Font.open(ufo_save_path)
    assert set(ufo.layers.keys()) == {"public.default", "test"}
    for layer in ufo.layers:
        assert layer is not _LAYER_NOT_LOADED


def test_lazy_data_loading_saveas(ufo_UbuTestData: Font, tmp_path: Path) -> None:
    ufo = ufo_UbuTestData
    ufo_path = tmp_path / "UbuTestData2.ufo"
    ufo.save(ufo_path)
    assert all(v is not _DATA_NOT_LOADED for v in ufo.data._data.values())


def test_lazy_data_loading_inplace_no_load(ufo_UbuTestData: Font) -> None:
    ufo = ufo_UbuTestData
    ufo.save()
    assert all(v is _DATA_NOT_LOADED for v in ufo.data._data.values())


def test_lazy_data_loading_inplace_load_some(ufo_UbuTestData: Font) -> None:
    ufo = ufo_UbuTestData
    some_data = b"abc"
    ufo.data["com.github.fonttools.ttx/T_S_I__0.ttx"] = some_data
    ufo.save()
    assert all(
        v is _DATA_NOT_LOADED for k, v in ufo.data._data.items() if "T_S_I__0" not in k
    )
    assert ufo.data["com.github.fonttools.ttx/T_S_I__0.ttx"] == some_data


def test_deepcopy_lazy_object(datadir: Path) -> None:
    path = datadir / "UbuTestData.ufo"
    font1 = ufoLib2.Font.open(path, lazy=True)

    font2 = deepcopy(font1)

    assert font1 is not font2
    assert font1 == font2

    assert font1.layers is not font2.layers
    assert font1.layers == font2.layers

    assert font1.layers.defaultLayer is not font2.layers.defaultLayer
    assert font1.layers.defaultLayer == font2.layers.defaultLayer

    assert font1.data is not font2.data
    assert font1.data == font2.data

    assert font1.images is not font2.images
    assert font1.images == font2.images

    assert font1.reader is not None
    assert not font1.reader.fs.isclosed()
    assert not font1._lazy

    assert font2.reader is None
    assert not font2._lazy

    assert font1.path == path
    assert font2.path is None


def test_unlazify(datadir: Path) -> None:
    reader = ufoLib.UFOReader(datadir / "UbuTestData.ufo")
    font = ufoLib2.Font.read(reader, lazy=True)

    assert font._reader is reader
    assert not reader.fs.isclosed()

    font.unlazify()

    assert font._lazy is False


def test_auto_unlazify_font(datadir: Path) -> None:
    font1 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=True)
    font2 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=False)

    assert font1 == font2


def test_auto_unlazify_data(datadir: Path) -> None:
    font1 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=True)
    font2 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=False)

    assert font1.data == font2.data


def test_auto_unlazify_images(datadir: Path) -> None:
    font1 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=True)
    font2 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=False)

    assert font1.images == font2.images


def test_font_eq_and_ne(ufo_UbuTestData: Font) -> None:
    font1 = ufo_UbuTestData
    font2 = deepcopy(font1)

    assert font1 == font2

    font1["a"].contours[0].points[0].x = 0

    assert font1 != font2


def test_empty_layerset() -> None:
    with pytest.raises(ValueError):
        LayerSet(layers={}, defaultLayer=None)  # type: ignore


def test_default_layerset() -> None:
    layers = LayerSet.default()
    assert len(layers) == 1
    assert "public.default" in layers
    assert len(layers["public.default"]) == 0
    assert layers["public.default"].default


def test_custom_layerset() -> None:
    default = Layer()
    ls1 = LayerSet.from_iterable([default])
    assert next(iter(ls1)) is ls1.defaultLayer

    with pytest.raises(ValueError, match="no layer marked as default"):
        LayerSet.from_iterable([Layer(name="abc")])

    with pytest.raises(ValueError, match="no layer marked as default"):
        LayerSet({"abc": Layer(name="abc")})

    with pytest.raises(ValueError, match="more than one layer marked as default"):
        LayerSet.from_iterable([Layer("a", default=True), Layer("b", default=True)])

    with pytest.raises(ValueError, match="more than one layer marked as default"):
        LayerSet({"a": Layer("a", default=True), "b": Layer("b", default=True)})

    with pytest.raises(KeyError, match="duplicate layer name"):
        LayerSet.from_iterable([Layer("a", default=True), Layer("a")])

    with pytest.raises(ValueError, match="default layer .* must be in layer set"):
        LayerSet(layers={"public.default": Layer()}, defaultLayer=Layer())

    # defaultLayerName is deprecated but still works for now
    ls2 = LayerSet.from_iterable([Layer(name="abc")], defaultLayerName="abc")
    assert ls2["abc"].default
    assert ls2["abc"] is ls2.defaultLayer

    # defaultLayer is set automatically based on Layer.default attribute
    ls3 = LayerSet.from_iterable([Layer(name="abc", default=True), Layer("def")])
    assert ls3["abc"].default
    assert ls3["abc"] is ls3.defaultLayer
    assert not ls3["def"].default

    # also for the default constructor, defaultLayer is guessed from Layer.default
    ls4 = LayerSet(layers={"foreground": Layer("foreground", default=True)})
    assert ls4["foreground"] is ls4.defaultLayer

    # unless defaultLayer parameter is set explicitly
    defaultLayer = Layer("foreground", default=True)
    ls5 = LayerSet(layers={"foreground": defaultLayer}, defaultLayer=defaultLayer)
    assert ls5["foreground"] is ls5.defaultLayer
    assert ls5.defaultLayer is defaultLayer


def test_change_default_layer() -> None:
    font = Font(layers=[Layer("foo", default=True), Layer("bar")])
    assert font.layers.defaultLayer is font.layers["foo"]
    assert font.layers["foo"].default
    assert not font.layers["bar"].default

    font.layers.defaultLayer = font.layers["bar"]
    assert font.layers.defaultLayer is font.layers["bar"]
    assert not font.layers["foo"].default
    assert font.layers["bar"].default

    font.newLayer("baz", default=True)
    assert font.layers.defaultLayer is font.layers["baz"]
    assert font.layers["baz"].default
    assert not font.layers["foo"].default
    assert not font.layers["bar"].default

    font.renameLayer("foo", "public.default")
    assert "foo" not in font.layers
    assert font.layers.defaultLayer is font.layers["public.default"]
    assert font.layers["public.default"].default
    assert not font.layers["baz"].default


def test_change_default_layer_invalid() -> None:
    font = Font(layers=[Layer(), Layer("background")])

    with pytest.raises(
        ValueError,
        match="there's already a layer named 'public.default' which must stay default",
    ):
        font.layers.defaultLayer = font.layers["background"]

    with pytest.raises(
        ValueError, match="Layer .* not found in layer set; can't set as default"
    ):
        font.layers.defaultLayer = Layer("foobar")


def test_guidelines() -> None:
    font = ufoLib2.Font()

    # accept either a mapping or a Guideline object
    font.appendGuideline({"x": 100, "y": 50, "angle": 315})
    font.appendGuideline(ufoLib2.objects.Guideline(x=30))

    assert len(font.guidelines) == 2
    assert font.guidelines == [
        ufoLib2.objects.Guideline(x=100, y=50, angle=315),
        ufoLib2.objects.Guideline(x=30),
    ]

    # setter should clear existing guidelines
    font.guidelines = [{"x": 100}, ufoLib2.objects.Guideline(y=20)]  # type: ignore

    assert len(font.guidelines) == 2
    assert font.guidelines == [
        ufoLib2.objects.Guideline(x=100),
        ufoLib2.objects.Guideline(y=20),
    ]


def test_woff_metadata(datadir: Path, tmp_path: Path) -> None:
    # The WoffMetadataTest.ufo contains all the WOFF metadata, here we check
    # that ufoLib validators accept the data and can read/write fontinfo.plist.
    input_path = datadir / "WoffMetadataTest.ufo"
    output_path = tmp_path / "WoffMetadataTest.ufo"

    font = Font.open(input_path, validate=True)
    font.save(output_path, validate=True)

    assert (input_path / "fontinfo.plist").read_text("utf-8") == (
        (output_path / "fontinfo.plist").read_text("utf-8")
    )


def test_features_normalize_newlines() -> None:
    assert Features("a\r\nb\rc\n").normalize_newlines().text == "a\nb\nc\n"


@pytest.mark.parametrize(
    "klass, attr_name, attr_type, obj",
    [
        (Font, "lib", Lib, {"foo": 1}),
        (Font, "kerning", Kerning, {("a", "b"): -10}),
        (Glyph, "lib", Lib, {"bar": [2, 3]}),
    ],
)
def test_convert_on_setattr(
    klass: Type[Any], attr_name: str, attr_type: Type[Any], obj: Any
) -> None:
    o = klass()
    assert isinstance(getattr(o, attr_name), attr_type)
    assert not isinstance(obj, attr_type)
    setattr(o, attr_name, obj)
    assert isinstance(getattr(o, attr_name), attr_type)
