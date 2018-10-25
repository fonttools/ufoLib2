import attr
from typing import Optional
from ufoLib2.objects.misc import Transformation

try:
    from collections.abc import Mapping  # python >= 3.3
except ImportError:
    from collections import Mapping


def _to_transformation(v):
    if not isinstance(v, Transformation):
        return Transformation(*v)
    return v


@attr.s(slots=True)
class Image(Mapping):
    fileName = attr.ib(default=None, type=Optional[str])
    _transformation = attr.ib(
        default=Transformation(),
        convert=_to_transformation,
        type=Transformation,
    )
    color = attr.ib(default=None, type=Optional[str])

    @property
    def transformation(self):
        return self._transformation

    @transformation.setter
    def transformation(self, value):
        self._transformation = _to_transformation(value)

    def clear(self):
        self.fileName = None
        self._transformation = None
        self.color = None

    def __bool__(self):
        # Glyph.image evaluates to False if no fileName is set
        return self.fileName is not None

    # alias for python 2
    __nonzero__ = __bool__

    _valid_keys_ = ("fileName",) + tuple(Transformation._fields) + ("color",)

    # implementation of collections.abc.Mapping abstract methods.
    # the fontTools.ufoLib.validators.imageValidator requires that image is a
    # subclass of Mapping...

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            return getattr(self.transformation, key)
        except AttributeError:
            raise KeyError(key)

    def __len__(self):
        return len(self._valid_keys_)

    def __iter__(self):
        return iter(self._valid_keys_)
