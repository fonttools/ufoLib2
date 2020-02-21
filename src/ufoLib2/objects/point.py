from typing import Optional, Union

import attr


@attr.s(slots=True)
class Point:
    x = attr.ib(type=Union[int, float])
    y = attr.ib(type=Union[int, float])
    type = attr.ib(default=None, type=Optional[str])
    smooth = attr.ib(default=False, type=bool)
    name = attr.ib(default=None, type=Optional[str])
    identifier = attr.ib(default=None, type=Optional[str])

    @property
    def segmentType(self):
        # alias for backward compatibility with defcon API
        return self.type

    def move(self, delta):
        x, y = delta
        self.x += x
        self.y += y
