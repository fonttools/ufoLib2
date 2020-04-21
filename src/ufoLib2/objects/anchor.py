from typing import Optional, Tuple

import attr

from ufoLib2.objects.misc import AttrDictMixin
from ufoLib2.typing import Number


@attr.s(auto_attribs=True, slots=True)
class Anchor(AttrDictMixin):
    """Represents a single anchor.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#anchor.
    """

    x: Number
    """The x coordinate of the anchor."""

    y: Number
    """The y coordinate of the anchor."""

    name: Optional[str] = None
    """The name of the anchor."""

    color: Optional[str] = None
    """The color of the anchor."""

    identifier: Optional[str] = None
    """The globally unique identifier of the anchor."""

    def move(self, delta: Tuple[Number, Number]) -> None:
        """Moves anchor by (x, y) font units."""
        x, y = delta
        self.x += x
        self.y += y
