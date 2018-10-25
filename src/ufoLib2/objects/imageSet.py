from ufoLib2.objects.misc import DataStore
from fontTools.ufoLib import UFOReader
from fontTools.ufoLib import UFOWriter


class ImageSet(DataStore):
    listdir = UFOReader.getImageDirectoryListing
    readf = UFOReader.readImage
    writef = UFOWriter.writeImage
    deletef = UFOWriter.removeImage
