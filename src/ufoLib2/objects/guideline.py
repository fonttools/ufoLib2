from __future__ import annotations

from typing import Optional

from attrs import define

from ufoLib2.objects.misc import AttrDictMixin
from ufoLib2.serde import serde


@serde
@define
class Guideline(AttrDictMixin):
    """Represents a single guideline.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#guideline. Has some
    data composition restrictions.
    """

    x: float = 0
    """The origin x coordinate of the guideline."""

    y: float = 0
    """The origin y coordinate of the guideline."""

    angle: float = 0
    """The angle of the guideline."""

    name: Optional[str] = None
    """The name of the guideline, no uniqueness required."""

    color: Optional[str] = None
    """The color of the guideline."""

    identifier: Optional[str] = None
    """The globally unique identifier of the guideline."""

    def __attrs_post_init__(self) -> None:
        if not (0 <= self.angle <= 360):
            raise ValueError("angle must be between 0 and 360")
