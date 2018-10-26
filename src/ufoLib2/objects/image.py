from fontTools.misc.transform import Identity, Transform

try:
    from collections.abc import Mapping  # python >= 3.3
except ImportError:
    from collections import Mapping
from ufoLib2.objects.misc import AttrReprMixin


class Image(AttrReprMixin, Mapping):
    __slots__ = _fields = ("fileName", "transformation", "color")

    def __init__(self, fileName=None, transformation=Identity, color=None):
        self.fileName = fileName
        if isinstance(transformation, Transform):
            self.transformation = transformation
        else:
            self.transformation = Transform(*transformation)
        self.color = color

    def clear(self):
        self.fileName = None
        self.transformation = Identity
        self.color = None

    def __bool__(self):
        # Glyph.image evaluates to False if no fileName is set
        return self.fileName is not None

    # alias for python 2
    __nonzero__ = __bool__

    _transformation_keys_ = (
        "xScale",
        "xyScale",
        "yxScale",
        "yScale",
        "xOffset",
        "yOffset",
    )
    _valid_keys_ = ("fileName",) + _transformation_keys_ + ("color",)

    # implementation of collections.abc.Mapping abstract methods.
    # the fontTools.ufoLib.validators.imageValidator requires that image is a
    # subclass of Mapping...

    def __getitem__(self, key):
        try:
            i = self._transformation_keys_.index(key)
        except ValueError:
            try:
                return getattr(self, key)
            except AttributeError:
                raise KeyError(key)
        else:
            return self.transformation[i]

    def __len__(self):
        return len(self._valid_keys_)

    def __iter__(self):
        return iter(self._valid_keys_)
