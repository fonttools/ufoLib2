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
