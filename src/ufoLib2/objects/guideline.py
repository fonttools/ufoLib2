from typing import Optional

import attr

from ufoLib2.objects.misc import AttrDictMixin
from ufoLib2.typing import Number


@attr.s(auto_attribs=True, slots=True)
class Guideline(AttrDictMixin):
    x: Optional[Number] = None
    y: Optional[Number] = None
    angle: Optional[Number] = None
    name: Optional[str] = None
    color: Optional[str] = None
    identifier: Optional[str] = None

    def __attrs_post_init__(self):
        x, y, angle = self.x, self.y, self.angle
        if x is None and y is None:
            raise ValueError("x or y must be present")
        if x is None or y is None:
            if angle is not None:
                raise ValueError("if 'x' or 'y' are None, 'angle' must not be present")
        if x is not None and y is not None and angle is None:
            raise ValueError("if 'x' and 'y' are defined, 'angle' must be defined")
        if angle is not None and not (0 <= angle <= 360):
            raise ValueError("angle must be between 0 and 360")
