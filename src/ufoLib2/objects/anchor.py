from typing import Optional, Tuple

import attr

from ufoLib2.objects.misc import AttrDictMixin
from ufoLib2.typing import Number


@attr.s(auto_attribs=True, slots=True)
class Anchor(AttrDictMixin):
    x: Number
    y: Number
    name: Optional[str] = None
    color: Optional[str] = None
    identifier: Optional[str] = None

    def move(self, delta: Tuple[Number, Number]) -> None:
        x, y = delta
        self.x += x
        self.y += y
