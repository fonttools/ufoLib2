from fontTools.ufoLib import UFOReader, UFOWriter

from ufoLib2.objects.misc import DataStore


class DataSet(DataStore):
    listdir = UFOReader.getDataDirectoryListing
    readf = UFOReader.readData
    writef = UFOWriter.writeData
    deletef = UFOWriter.removeData
