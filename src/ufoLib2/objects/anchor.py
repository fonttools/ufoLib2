from typing import Optional, Union

import attr

from ufoLib2.objects.misc import AttrDictMixin


@attr.s(slots=True)
class Anchor(AttrDictMixin):
    x = attr.ib(type=Union[int, float])
    y = attr.ib(type=Union[int, float])
    name = attr.ib(default=None, type=Optional[str])
    color = attr.ib(default=None, type=Optional[str])
    identifier = attr.ib(default=None, type=Optional[str])

    def move(self, delta):
        x, y = delta
        self.x += x
        self.y += y
