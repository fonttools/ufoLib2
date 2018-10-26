from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.misc import AttrDictMixin
from fontTools.ufoLib import fontInfoAttributesVersion3


def _guidelinesConverter(lst):
    result = []
    for g in lst:
        if isinstance(g, Guideline):
            result.append(g)
        else:
            result.append(Guideline(**g))
    return result


class Info(AttrDictMixin):
    __slots__ = _fields = sorted(fontInfoAttributesVersion3)

    def __init__(self, **kwargs):
        for key in self.__slots__:
            setattr(self, key, kwargs.pop(key, None))
        if any(kwargs):
            more = len(kwargs) > 1
            s = "s" if more else ""
            an = "" if more else "an "
            raise TypeError(
                "__init__ got {}unexpected keyword argument{}: {}".format(
                    an, s, ", ".join(repr(k) for k in kwargs)
                )
            )
