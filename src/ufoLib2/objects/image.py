from collections.abc import Mapping
from typing import Optional
import attr
from fontTools.misc.transform import Identity, Transform


def _convert_transform(t) -> Transform:
    return t if isinstance(t, Transform) else Transform(*t)


@attr.s(slots=True)
class Image(Mapping):
    fileName = attr.ib(default=None, type=Optional[str])
    transformation = attr.ib(
        default=Identity, converter=_convert_transform, type=Transform
    )
    color = attr.ib(default=None, type=Optional[str])

    def clear(self):
        self.fileName = None
        self.transformation = Identity
        self.color = None

    def __bool__(self):
        # Glyph.image evaluates to False if no fileName is set
        return self.fileName is not None

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
