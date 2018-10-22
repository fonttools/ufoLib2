import ufoLib2
from fontTools.misc.py23 import basestring


def test_import_version():
    assert hasattr(ufoLib2, "__version__")
    assert isinstance(ufoLib2.__version__, basestring)
