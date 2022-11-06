from __future__ import annotations

from typing import Any, Optional


class Error(Exception):
    """The base exception for ufoLib2."""


class ExtrasNotInstalledError(Error):
    """The extras required for this feature are not installed."""

    def __init__(self, extras: str, *, chained: Optional[Exception] = None) -> None:
        super().__init__(f"Extras not installed: {extras!r}")
        self.chained = chained

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        raise self from self.chained
