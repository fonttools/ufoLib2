import ufoLib2


def test_import_version():
    assert hasattr(ufoLib2, "__version__")
    assert isinstance(ufoLib2.__version__, str)
