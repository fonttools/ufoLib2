from fontTools.ufoLib import UFOReader, UFOWriter

from ufoLib2.objects.misc import DataStore


class ImageSet(DataStore):
    listdir = UFOReader.getImageDirectoryListing
    readf = UFOReader.readImage
    writef = UFOWriter.writeImage
    deletef = UFOWriter.removeImage
