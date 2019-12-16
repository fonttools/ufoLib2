import os
import shutil
from typing import Any, Mapping, Union

import attr
import fs.tempfs
from fontTools.ufoLib import UFOFileStructure, UFOReader, UFOWriter

from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.objects.dataSet import DataSet
from ufoLib2.objects.features import Features
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.imageSet import ImageSet
from ufoLib2.objects.info import Info
from ufoLib2.objects.layerSet import LayerSet
from ufoLib2.objects.misc import _deepcopy_unlazify_attrs


def _convert_Info(value: Union[Info, Mapping[str, Any]]) -> Info:
    return value if isinstance(value, Info) else Info(**value)


def _convert_DataSet(value: Union[DataSet, Mapping[str, Any]]) -> DataSet:
    return value if isinstance(value, DataSet) else DataSet(**value)


def _convert_ImageSet(value: Union[ImageSet, Mapping[str, Any]]) -> ImageSet:
    return value if isinstance(value, ImageSet) else ImageSet(**value)


def _convert_Features(value: Union[Features, str]) -> Features:
    return value if isinstance(value, Features) else Features(value)


@attr.s(slots=True, repr=False, eq=False)
class Font:
    # this is the only positional argument, and it is added for compatibility with
    # the defcon-style Font(path) constructor. If defcon compatibility is not a concern
    # we recommend to use the alternative `open` classmethod constructor.
    _path = attr.ib(default=None, metadata=dict(copyable=False))

    layers = attr.ib(
        default=attr.Factory(LayerSet),
        validator=attr.validators.instance_of(LayerSet),
        type=LayerSet,
        kw_only=True,
    )
    info = attr.ib(
        default=attr.Factory(Info), converter=_convert_Info, type=Info, kw_only=True
    )
    features = attr.ib(
        default=attr.Factory(Features),
        converter=_convert_Features,
        type=Features,
        kw_only=True,
    )
    groups = attr.ib(default=attr.Factory(dict), type=dict, kw_only=True)
    kerning = attr.ib(default=attr.Factory(dict), type=dict, kw_only=True)
    lib = attr.ib(default=attr.Factory(dict), type=dict, kw_only=True)
    data = attr.ib(
        default=attr.Factory(DataSet),
        converter=_convert_DataSet,
        type=DataSet,
        kw_only=True,
    )
    images = attr.ib(
        default=attr.Factory(ImageSet),
        converter=_convert_ImageSet,
        type=ImageSet,
        kw_only=True,
    )

    _lazy = attr.ib(default=None, kw_only=True)
    _validate = attr.ib(default=True, kw_only=True)

    _reader = attr.ib(default=None, kw_only=True, init=False)
    _fileStructure = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        if self._path is not None:
            # if lazy argument is not set, default to lazy=True if path is provided
            if self._lazy is None:
                self._lazy = True
            reader = UFOReader(self._path, validate=self._validate)
            self.layers = LayerSet.read(reader, lazy=self._lazy)
            self.data = DataSet.read(reader, lazy=self._lazy)
            self.images = ImageSet.read(reader, lazy=self._lazy)
            self.info = Info.read(reader)
            self.features = Features(reader.readFeatures())
            self.groups = reader.readGroups()
            self.kerning = reader.readKerning()
            self.lib = reader.readLib()
            self._fileStructure = reader.fileStructure
            if self._lazy:
                # keep the reader around so we can close it when done
                self._reader = reader

    @classmethod
    def open(cls, path, lazy=True, validate=True):
        reader = UFOReader(path, validate=validate)
        self = cls.read(reader, lazy=lazy)
        self._path = path
        if not lazy:
            reader.close()
        return self

    @classmethod
    def read(cls, reader, lazy=True):
        self = cls(
            layers=LayerSet.read(reader, lazy=lazy),
            data=DataSet.read(reader, lazy=lazy),
            images=ImageSet.read(reader, lazy=lazy),
            info=Info.read(reader),
            features=Features(reader.readFeatures()),
            groups=reader.readGroups(),
            kerning=reader.readKerning(),
            lib=reader.readLib(),
            lazy=lazy,
        )
        self._fileStructure = reader.fileStructure
        if lazy:
            # keep the reader around so we can close it when done
            self._reader = reader
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
            self.__class__.__module__, self.__class__.__name__, fontName, hex(id(self))
        )

    def __eq__(self, other):
        # same as attrs-defined __eq__ method, only that it un-lazifies fonts if needed
        if other.__class__ is not self.__class__:
            return NotImplemented

        for font in (self, other):
            if font._lazy:
                font.unlazify()

        return (
            self.layers,
            self.info,
            self.features,
            self.groups,
            self.kerning,
            self.lib,
            self.data,
            self.images,
        ) == (
            other.layers,
            other.info,
            other.features,
            other.groups,
            other.kerning,
            other.lib,
            other.data,
            other.images,
        )

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    @property
    def reader(self):
        return self._reader

    def unlazify(self):
        if self._lazy:
            assert self._reader is not None
            self.layers.unlazify()
            self.data.unlazify()
            self.images.unlazify()
        self._lazy = False

    __deepcopy__ = _deepcopy_unlazify_attrs

    @property
    def glyphOrder(self):
        return list(self.lib.get("public.glyphOrder", []))

    @glyphOrder.setter
    def glyphOrder(self, value):
        if value is None or len(value) == 0:
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
        return self._path

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
        self, path=None, formatVersion=3, structure=None, overwrite=False, validate=True
    ):
        if formatVersion != 3:
            raise NotImplementedError("unsupported format version: %s" % formatVersion)
        # validate 'structure' argument
        if structure is not None:
            structure = UFOFileStructure(structure)
        elif self._fileStructure is not None:
            # if structure is None, fall back to the same as when first loaded
            structure = self._fileStructure

        if hasattr(path, "__fspath__"):
            path = path.__fspath__()
        if isinstance(path, str):
            path = os.path.normpath(path)
        # else we assume it's an fs.BaseFS and we pass it on to UFOWriter

        overwritePath = tmp = None

        saveAs = path is not None
        if saveAs:
            if isinstance(path, str) and os.path.exists(path):
                if overwrite:
                    overwritePath = path
                    tmp = fs.tempfs.TempFS()
                    path = tmp.getsyspath(os.path.basename(path))
                else:
                    import errno

                    raise OSError(errno.EEXIST, "path %r already exists" % path)
        elif self.path is None:
            raise TypeError("'path' is required when saving a new Font")
        else:
            path = self.path

        try:
            with UFOWriter(path, structure=structure, validate=validate) as writer:
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
