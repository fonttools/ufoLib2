import py
import pytest
import ufoLib2


@pytest.fixture
def datadir(request):
    return py.path.local(request.fspath.dirname).join("data")


@pytest.fixture
def ufo_UbuTestData(tmpdir, datadir):
    ufo_path = tmpdir.join("UbuTestData.ufo")
    datadir.join("UbuTestData.ufo").copy(ufo_path)
    return ufoLib2.Font.open(str(ufo_path))
