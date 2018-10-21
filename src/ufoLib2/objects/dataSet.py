from ufoLib2.objects.misc import DataStore
from fontTools.ufoLib import UFOReader
from fontTools.ufoLib import UFOWriter


class DataSet(DataStore):
    readf = UFOReader.readData
    writef = UFOWriter.writeData
    deletef = UFOWriter.removeData
