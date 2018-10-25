import attr
from collections import OrderedDict
from ufoLib2.objects.layer import Layer
from ufoLib2.constants import DEFAULT_LAYER_NAME


def _layersConverter(value):
    # takes an iterable of Layer objects and returns an OrderedDict keyed
    # by layer name
    layers = OrderedDict()
    for layer in value:
        if not isinstance(layer, Layer):
            raise TypeError(
                "expected 'Layer', found '%s'" % type(layer).__name__
            )
        if layer.name in layers:
            raise KeyError("duplicate layer name: '%s'" % layer.name)
        layers[layer.name] = layer
    return layers


@attr.s(slots=True, repr=False)
class LayerSet(object):
    _layers = attr.ib(default=(), converter=_layersConverter, type=OrderedDict)
    defaultLayer = attr.ib(default=None, type=Layer)

    _scheduledForDeletion = attr.ib(
        default=attr.Factory(set), init=False, repr=False
    )

    def __attrs_post_init__(self):
        if not self._layers:
            # LayerSet is never empty; always contains at least the default
            if self.defaultLayer is not None:
                raise TypeError(
                    "'defaultLayer' argument is invalid with empty LayerSet"
                )
            self.defaultLayer = self.newLayer(DEFAULT_LAYER_NAME)
        elif self.defaultLayer is not None:
            # check that the specified default layer is in the layer set;
            default = self.defaultLayer
            for layer in self._layers.values():
                if layer is default:
                    break
            else:
                raise ValueError(
                    "defaultLayer %r is not among the specified layers"
                    % default
                )
        elif len(self._layers) == 1:
            # there's only one, we assume it's the default
            self.defaultLayer = next(self._layers.values())
        else:
            if DEFAULT_LAYER_NAME not in self._layers:
                raise ValueError("default layer not specified")
            self.defaultLayer = self._layers[DEFAULT_LAYER_NAME]

    @classmethod
    def read(cls, reader, lazy=True):
        defaultLayerName = reader.getDefaultLayerName()

        layers = []
        hasDefaultKeyword = None
        defaultLayer = None

        for layerName in reader.getLayerNames():
            isDefault = layerName == defaultLayerName
            # UFOReader.getGlyphSet method does not support the 'defaultLayer'
            # keyword argument, whereas the UFOWriter.getGlyphSet method
            # requires it. In order to allow to use an instance of UFOWriter
            # as the 'reader', here we try both ways...
            if hasDefaultKeyword is None:
                try:
                    glyphSet = reader.getGlyphSet(
                        layerName, defaultLayer=isDefault
                    )
                except TypeError as e:
                    if "unexpected keyword argument 'defaultLayer'" in str(e):
                        glyphSet = reader.getGlyphSet(layerName)
                    hasDefaultKeyword = False
                else:
                    hasDefaultKeyword = True
            elif hasDefaultKeyword:
                glyphSet = reader.getGlyphSet(
                    layerName, defaultLayer=isDefault
                )
            else:
                glyphSet = reader.getGlyphSet(layerName)

            layer = Layer.read(layerName, glyphSet, lazy=lazy)
            if isDefault:
                defaultLayer = layer
            layers.append(layer)

        assert defaultLayer is not None

        return cls(layers, defaultLayer=defaultLayer)

    def __contains__(self, name):
        return name in self._layers

    def __delitem__(self, name):
        if name == self.defaultLayer.name:
            raise KeyError("cannot delete default layer %r" % name)
        del self._layers[name]
        self._scheduledForDeletion.add(name)

    def __getitem__(self, name):
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
        return "%s(%s)" % (
            self.__class__.__name__,
            repr(list(self)) if self._layers else "",
        )

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
        if name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(name)
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
        self._scheduledForDeletion.add(name)
        if newName in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(newName)
        layer._name = newName

    def write(self, writer, saveAs=True):
        # if in-place, remove deleted layers
        if not saveAs:
            for layerName in self._scheduledForDeletion:
                writer.deleteGlyphSet(layerName)
        # write layers
        defaultLayer = self.defaultLayer
        for layer in self:
            default = layer is defaultLayer
            glyphSet = writer.getGlyphSet(layer.name, defaultLayer=default)
            layer.write(glyphSet, saveAs=saveAs)
        writer.writeLayerContents(self.layerOrder)
        self._scheduledForDeletion = set()
