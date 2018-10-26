from ufoLib2.objects.misc import AttrReprMixin


class Point(AttrReprMixin):
    __slots__ = _fields = (
        "x",
        "y",
        "segmentType",
        "smooth",
        "name",
        "identifier",
    )

    def __init__(
        self, x, y, segmentType=None, smooth=False, name=None, identifier=None
    ):
        self.x = x
        self.y = y
        self.segmentType = segmentType
        self.smooth = smooth
        self.name = name
        self.identifier = identifier
