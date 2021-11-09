from __future__ import annotations

from attr import define

from ufoLib2.objects.misc import AttrDictMixin


@define
class Anchor(AttrDictMixin):
    """Represents a single anchor.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#anchor.
    """

    x: float
    """The x coordinate of the anchor."""

    y: float
    """The y coordinate of the anchor."""

    name: str | None = None
    """The name of the anchor."""

    color: str | None = None
    """The color of the anchor."""

    identifier: str | None = None
    """The globally unique identifier of the anchor."""

    def move(self, delta: tuple[float, float]) -> None:
        """Moves anchor by (x, y) font units."""
        x, y = delta
        self.x += x
        self.y += y
