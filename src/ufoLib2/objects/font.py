import attr
import os
import shutil
import fs.tempfs
from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.objects.dataSet import DataSet
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.imageSet import ImageSet
from ufoLib2.objects.info import Info
from ufoLib2.objects.layerSet import LayerSet
from ufoLib2.objects.features import Features
from fontTools.misc.py23 import basestring, PY3
from fontTools.ufoLib import UFOReader, UFOWriter, UFOFileStructure


@attr.s(slots=True, kw_only=PY3, repr=False)
class Font(object):
    layers = attr.ib(
        default=attr.Factory(LayerSet),
        validator=attr.validators.instance_of(LayerSet),
        type=LayerSet,
    )
    info = attr.ib(
        default=attr.Factory(Info),
        converter=lambda v: v if isinstance(v, Info) else Info(**v),
        type=Info,
    )
    features = attr.ib(
        default=attr.Factory(Features),
        converter=lambda v: v if isinstance(v, Features) else Features(v),
        type=Features,
    )
    groups = attr.ib(default=attr.Factory(dict), type=dict)
    kerning = attr.ib(default=attr.Factory(dict), type=dict)
    lib = attr.ib(default=attr.Factory(dict), type=dict)
    data = attr.ib(
        default=attr.Factory(DataSet),
        converter=lambda v: v if isinstance(v, DataSet) else DataSet(**v),
        type=DataSet,
    )
    images = attr.ib(
        default=attr.Factory(ImageSet),
        converter=lambda v: v if isinstance(v, ImageSet) else ImageSet(**v),
        type=ImageSet,
    )

    _path = attr.ib(default=None, init=False)
    _reader = attr.ib(default=None, init=False)
    _fileStructure = attr.ib(default=None, init=False)

    @classmethod
    def open(cls, path, lazy=True, validate=True):
        reader = UFOReader(path, validate=validate)
        self = cls.read(reader, lazy=lazy)
        self._path = path
        self._fileStructure = reader.fileStructure
        if lazy:
            # keep the reader around so we can close it when done
            self._reader = reader
        else:
            reader.close()
        return self

    @classmethod
    def read(cls, reader, lazy=True):
        layers = LayerSet.read(reader, lazy=lazy)
        data = DataSet.read(reader, lazy=lazy)
        images = ImageSet.read(reader, lazy=lazy)
        info = Info()
        reader.readInfo(info)
        features = Features(reader.readFeatures())
        groups = reader.readGroups()
        kerning = reader.readKerning()
        lib = reader.readLib()
        self = cls(
            layers=layers,
            info=info,
            features=features,
            groups=groups,
            kerning=kerning,
            lib=lib,
            data=data,
            images=images,
        )
        return self

    def __contains__(self, name):
        return name in self.layers.defaultLayer

    def __delitem__(self, name):
        del self.layers.defaultLayer[name]

    def __getitem__(self, name):
        return self.layers.defaultLayer[name]

    def __setitem__(self, name, glyph):
        self.layers.defaultLayer[name] = glyph

    def __iter__(self):
        return iter(self.layers.defaultLayer)

    def __len__(self):
        return len(self.layers.defaultLayer)

    def get(self, name, default=None):
        return self.layers.defaultLayer.get(name, default)

    def keys(self):
        return self.layers.defaultLayer.keys()

    def close(self):
        if self._reader is not None:
            self._reader.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def __repr__(self):
        names = list(filter(None, [self.info.familyName, self.info.styleName]))
        fontName = " '{}'".format(" ".join(names)) if names else ""
        return "<{}.{}{} at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            fontName,
            hex(id(self)),
        )

    @property
    def reader(self):
        return self._reader

    @property
    def glyphOrder(self):
        return list(self.lib.get("public.glyphOrder", []))

    @glyphOrder.setter
    def glyphOrder(self, value):
        if value is None or len(value) == 0:
            value = 0
            if "public.glyphOrder" in self.lib:
                del self.lib["public.glyphOrder"]
        else:
            self.lib["public.glyphOrder"] = value

    @property
    def guidelines(self):
        if self.info.guidelines is None:
            return []
        return self.info.guidelines

    @guidelines.setter
    def guidelines(self, value):
        for guideline in value:
            self.appendGuideline(guideline)

    @property
    def path(self):
        try:
            return self._path
        except AttributeError:
            return

    def addGlyph(self, glyph):
        self.layers.defaultLayer.addGlyph(glyph)

    def newGlyph(self, name):
        return self.layers.defaultLayer.newGlyph(name)

    def newLayer(self, name, **kwargs):
        return self.layers.newLayer(name, **kwargs)

    def renameGlyph(self, name, newName, overwrite=False):
        self.layers.defaultLayer.renameGlyph(name, newName, overwrite)

    def renameLayer(self, name, newName, overwrite=False):
        self.layers.renameLayer(name, newName, overwrite)

    def appendGuideline(self, guideline):
        if not isinstance(guideline, Guideline):
            guideline = Guideline(**guideline)
        if self.info.guidelines is None:
            self.info.guidelines = []
        self.info.guidelines.append(guideline)

    def write(self, writer, saveAs=None):
        if saveAs is None:
            saveAs = self._reader is not writer
        # TODO move this check to fontTools UFOWriter
        if self.layers.defaultLayer.name != DEFAULT_LAYER_NAME:
            assert DEFAULT_LAYER_NAME not in self.layers.layerOrder
        # save font attrs
        writer.writeFeatures(self.features.text)
        writer.writeGroups(self.groups)
        writer.writeInfo(self.info)
        writer.writeKerning(self.kerning)
        writer.writeLib(self.lib)
        # save the layers
        self.layers.write(writer, saveAs=saveAs)
        # save bin parts
        self.data.write(writer, saveAs=saveAs)
        self.images.write(writer, saveAs=saveAs)

    def save(
        self,
        path=None,
        formatVersion=3,
        structure=None,
        overwrite=False,
        validate=True,
    ):
        if formatVersion != 3:
            raise NotImplementedError(
                "unsupported format version: %s" % formatVersion
            )
        # validate 'structure' argument
        if structure is not None:
            structure = UFOFileStructure(structure)
        elif self._fileStructure is not None:
            # if structure is None, fall back to the same as when first loaded
            structure = self._fileStructure

        if hasattr(path, "__fspath__"):
            path = path.__fspath__()
        if isinstance(path, basestring):
            path = os.path.normpath(path)
        # else we assume it's an fs.BaseFS and we pass it on to UFOWriter

        overwritePath = tmp = None

        saveAs = path is not None
        if saveAs:
            if isinstance(path, basestring) and os.path.exists(path):
                if overwrite:
                    overwritePath = path
                    tmp = fs.tempfs.TempFS()
                    path = tmp.getsyspath(os.path.basename(path))
                else:
                    import errno

                    raise OSError(
                        errno.EEXIST, "path %r already exists" % path
                    )
        elif self.path is None:
            raise TypeError("'path' is required when saving a new Font")
        else:
            path = self.path

        try:
            with UFOWriter(
                path, structure=structure, validate=validate
            ) as writer:
                self.write(writer, saveAs=saveAs)
            writer.setModificationTime()
        except Exception:
            raise
        else:
            if overwritePath is not None:
                # remove existing then move file to destination
                if os.path.isdir(overwritePath):
                    shutil.rmtree(overwritePath)
                elif os.path.isfile(overwritePath):
                    os.remove(overwritePath)
                shutil.move(path, overwritePath)
                path = overwritePath
        finally:
            # clean up the temporary directory
            if tmp is not None:
                tmp.close()

        self._path = path
