from typing import Optional, Tuple

import attr

from ufoLib2.typing import Number


@attr.s(auto_attribs=True, slots=True)
class Point:
    x: Number
    y: Number
    type: Optional[str] = None
    smooth: bool = False
    name: Optional[str] = None
    identifier: Optional[str] = None

    @property
    def segmentType(self):
        # alias for backward compatibility with defcon API
        return self.type

    def move(self, delta: Tuple[Number, Number]) -> None:
        x, y = delta
        self.x += x
        self.y += y
