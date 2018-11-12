import ufoLib2
from fontTools.misc.py23 import basestring


def test_import_version():
    assert hasattr(ufoLib2, "__version__")
    assert isinstance(ufoLib2.__version__, basestring)


def test_LayerSet_load_layers_on_iteration(tmpdir):
    from ufoLib2.objects.misc import _NOT_LOADED

    ufo = ufoLib2.Font()
    ufo.layers.newLayer("test")
    ufo_save_path = str(tmpdir.join("test.ufo"))
    ufo.save(ufo_save_path)
    ufo = ufoLib2.Font.open(ufo_save_path)
    for layer in ufo.layers:
        assert layer is not _NOT_LOADED
