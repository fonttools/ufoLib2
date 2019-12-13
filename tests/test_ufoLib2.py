from copy import deepcopy

from fontTools import ufoLib

import ufoLib2
from ufoLib2.objects.misc import _NOT_LOADED


def test_import_version():
    assert hasattr(ufoLib2, "__version__")
    assert isinstance(ufoLib2.__version__, str)


def test_LayerSet_load_layers_on_iteration(tmp_path):
    ufo = ufoLib2.Font()
    ufo.layers.newLayer("test")
    ufo_save_path = tmp_path / "test.ufo"
    ufo.save(ufo_save_path)
    ufo = ufoLib2.Font.open(ufo_save_path)
    for layer in ufo.layers:
        assert layer is not _NOT_LOADED


def test_lazy_data_loading_saveas(ufo_UbuTestData, tmp_path):
    ufo = ufo_UbuTestData
    ufo_path = tmp_path / "UbuTestData2.ufo"
    ufo.save(ufo_path)
    assert all(v is not _NOT_LOADED for v in ufo.data._data.values())


def test_lazy_data_loading_inplace_no_load(ufo_UbuTestData):
    ufo = ufo_UbuTestData
    ufo.save()
    assert all(v is _NOT_LOADED for v in ufo.data._data.values())


def test_lazy_data_loading_inplace_load_some(ufo_UbuTestData):
    ufo = ufo_UbuTestData
    some_data = b"abc"
    ufo.data["com.github.fonttools.ttx/T_S_I__0.ttx"] = some_data
    ufo.save()
    assert all(
        v is _NOT_LOADED for k, v in ufo.data._data.items() if "T_S_I__0" not in k
    )
    assert ufo.data["com.github.fonttools.ttx/T_S_I__0.ttx"] == some_data


def test_constructor_from_path(datadir):
    path = datadir / "UbuTestData.ufo"
    font = ufoLib2.Font(path)

    assert font._path == path
    assert font._lazy is True
    assert font._validate is True
    assert font._reader is not None

    font2 = ufoLib2.Font(path, lazy=False, validate=False)

    assert font2._path == path
    assert font2._lazy is False
    assert font2._validate is False
    assert font2._reader is None

    assert font == font2


def test_deepcopy_lazy_object(datadir):
    font1 = ufoLib2.Font.open(datadir / "UbuTestData.ufo", lazy=True)

    font2 = deepcopy(font1)

    assert font1 is not font2
    assert font1.layers is not font2.layers
    assert font1.layers.defaultLayer is not font2.layers.defaultLayer
    assert font1.data is not font2.data
    assert font1.images is not font2.images


def test_unlazify(datadir):
    reader = ufoLib.UFOReader(datadir / "UbuTestData.ufo")
    font = ufoLib2.Font.read(reader, lazy=True)

    assert font._reader is reader
    assert not reader.fs.isclosed()

    font.unlazify()  # close_reader=False by default

    assert font._reader is None
    assert not reader.fs.isclosed()


def test_unlazify_close_reader(datadir):
    reader = ufoLib.UFOReader(datadir / "UbuTestData.ufo")
    font = ufoLib2.Font.read(reader, lazy=True)

    assert font._reader is reader
    assert not reader.fs.isclosed()

    font.unlazify(close_reader=True)

    assert font._reader is None
    assert reader.fs.isclosed()


def test_font_eq_and_ne(ufo_UbuTestData):
    font1 = ufo_UbuTestData
    font2 = deepcopy(font1)

    assert font1 == font2

    font1["a"].contours[0].points[0].x = 0

    assert font1 != font2
