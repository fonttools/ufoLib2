from collections import OrderedDict
from ufoLib2.objects.misc import _NOT_LOADED
from ufoLib2.objects.layer import Layer
from ufoLib2.constants import DEFAULT_LAYER_NAME


class LayerSet(object):
    _fields = ("_layers", "defaultLayerName")
    __slots__ = ("_layers", "defaultLayer", "_reader")

    def __init__(self, layers=None, defaultLayerName=None):
        if not layers:
            # LayerSet is never empty; always contains at least the default
            if defaultLayerName is not None:
                raise TypeError(
                    "'defaultLayer' argument is invalid with empty LayerSet"
                )
            self._layers = OrderedDict()
            self.defaultLayer = self.newLayer(DEFAULT_LAYER_NAME)
        else:
            if not isinstance(layers, OrderedDict):
                layers = OrderedDict()
                for layer in layers:
                    if not isinstance(layer, Layer):
                        raise TypeError(
                            "expected 'Layer', found '%s'"
                            % type(layer).__name__
                        )
                    if layer.name in layers:
                        raise KeyError(
                            "duplicate layer name: '%s'" % layer.name
                        )
                    layers[layer.name] = layer
            self._layers = layers

            # check that the default layer is in the layer set
            if defaultLayerName is not None:
                if defaultLayerName not in self._layers:
                    raise ValueError(
                        "%r is not among the specified layers"
                        % defaultLayerName
                    )
                self.defaultLayer = self._layers[defaultLayerName]
            elif len(self._layers) == 1:
                # there's only one, we assume it's the default
                self.defaultLayer = next(self._layers.values())
            else:
                if DEFAULT_LAYER_NAME not in self._layers:
                    raise ValueError("default layer not specified")
                self.defaultLayer = self._layers[DEFAULT_LAYER_NAME]

        self._reader = None

    @classmethod
    def read(cls, reader, lazy=True):
        layers = OrderedDict()

        defaultLayerName = reader.getDefaultLayerName()

        for layerName in reader.getLayerNames():
            isDefault = layerName == defaultLayerName
            if isDefault or not lazy:
                layer = cls._loadLayer(reader, layerName, lazy, isDefault)
                layers[layerName] = layer
            else:
                layers[layerName] = _NOT_LOADED

        self = cls(layers, defaultLayerName=defaultLayerName)
        if lazy:
            self._reader = reader

        return self

    @staticmethod
    def _loadLayer(reader, layerName, lazy=True, default=False):
        # UFOReader.getGlyphSet method doesn't support 'defaultLayer'
        # keyword argument, whereas the UFOWriter.getGlyphSet method
        # requires it. In order to allow to use an instance of
        # UFOWriter as the 'reader', here we try both ways...
        try:
            glyphSet = reader.getGlyphSet(layerName, defaultLayer=default)
        except TypeError as e:
            # TODO use inspect module?
            if "keyword argument 'defaultLayer'" in str(e):
                glyphSet = reader.getGlyphSet(layerName)

        return Layer.read(layerName, glyphSet, lazy=lazy)

    def loadLayer(self, layerName, lazy=True, default=False):
        assert self._reader is not None
        if layerName not in self._layers:
            raise KeyError(layerName)
        layer = self._loadLayer(self._reader, layerName, lazy, default)
        self._layers[layerName] = layer
        return layer

    def __contains__(self, name):
        return name in self._layers

    def __delitem__(self, name):
        if name == self.defaultLayer.name:
            raise KeyError("cannot delete default layer %r" % name)
        del self._layers[name]

    def __getitem__(self, name):
        if self._layers[name] is _NOT_LOADED:
            return self.loadLayer(name)
        return self._layers[name]

    def __iter__(self):
        return iter(self._layers.values())

    def __len__(self):
        return len(self._layers)

    def get(self, name, default=None):
        return self._layers.get(name, default)

    def keys(self):
        return self._layers.keys()

    def __repr__(self):
        n = len(self._layers)
        return "<{}.{} ({} layer{}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            n,
            "s" if n > 1 else "",
            hex(id(self)),
        )

    @property
    def defaultLayerName(self):
        return self.defaultLayer.name

    @property
    def layerOrder(self):
        return list(self._layers)

    @layerOrder.setter
    def layerOrder(self, order):
        assert set(order) == set(self._layers)
        layers = OrderedDict()
        for name in order:
            layers[name] = self._layers[name]
        self._layers = layers

    def newLayer(self, name, **kwargs):
        if name in self._layers:
            raise KeyError("layer %r already exists" % name)
        self._layers[name] = layer = Layer(name, **kwargs)
        return layer

    def renameGlyph(self, name, newName, overwrite=False):
        # Note: this would be easier if the glyph contained the layers!
        if name == newName:
            return
        # make sure we're copying something
        if not any(name in layer for layer in self):
            raise KeyError("name %r is not in layer set" % name)
        # prepare destination, delete if overwrite=True or error
        for layer in self:
            if newName in self._layers:
                if overwrite:
                    del layer[newName]
                else:
                    raise KeyError("target name %r already exists" % newName)
        # now do the move
        for layer in self:
            if name in layer:
                layer[newName] = glyph = layer.pop(name)
                glyph._name = newName

    def renameLayer(self, name, newName, overwrite=False):
        if name == newName:
            return
        if not overwrite and newName in self._layers:
            raise KeyError("target name %r already exists" % newName)
        self._layers[newName] = layer = self._layers.pop(name)
        layer._name = newName

    def write(self, writer, saveAs=None):
        if saveAs is None:
            saveAs = self._reader is not writer
        # if in-place, remove deleted layers
        layers = self._layers
        if not saveAs:
            for name in set(writer.getLayerNames()).difference(layers):
                writer.deleteGlyphSet(name)
        # write layers
        defaultLayer = self.defaultLayer
        for name, layer in layers.items():
            default = layer is defaultLayer
            if layer is _NOT_LOADED:
                if saveAs:
                    layer = self.loadLayer(name, lazy=False)
                else:
                    continue
            glyphSet = writer.getGlyphSet(name, defaultLayer=default)
            layer.write(glyphSet, saveAs=saveAs)
        writer.writeLayerContents(self.layerOrder)
