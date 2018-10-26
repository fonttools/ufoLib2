from ufoLib2.objects.misc import AttrDictMixin


class Guideline(AttrDictMixin):
    __slots__ = _fields = ("x", "y", "angle", "name", "color", "identifier")

    def __init__(
        self,
        x=None,
        y=None,
        angle=None,
        name=None,
        color=None,
        identifier=None,
    ):
        if x is None and y is None:
            raise ValueError("x or y must be present")
        if x is None or y is None:
            if angle is not None:
                raise ValueError(
                    "if 'x' or 'y' are None, 'angle' must not be present"
                )
        if x is not None and y is not None and angle is None:
            raise ValueError(
                "if 'x' and 'y' are defined, 'angle' must be defined"
            )
        if angle is not None and not (0 <= angle <= 360):
            raise ValueError("angle must be between 0 and 360")
        self.x = x
        self.y = y
        self.angle = angle
        self.name = name
        self.color = color
        self.identifier = identifier
