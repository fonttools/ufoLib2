from ufoLib2.objects.misc import AttrDictMixin


class Anchor(AttrDictMixin):
    __slots__ = _fields = ("x", "y", "name", "color", "identifier")

    def __init__(self, x, y, name=None, color=None, identifier=None):
        self.x = x
        self.y = y
        self.name = name
        self.color = color
        self.identifier = identifier
