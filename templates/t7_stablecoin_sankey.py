"""T7: Cross-chain stablecoin flow Sankey chart template."""

from __future__ import annotations

from datetime import date
from pathlib import Path


def render(as_of: date | str | None = None, variant: str | None = None) -> Path:
    """Render T7 through the requested cutoff date and return the PNG path."""
    raise NotImplementedError("T7 stablecoin Sankey rendering is not implemented yet.")
