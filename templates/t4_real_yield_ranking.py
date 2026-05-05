"""T4: LP and staking real-yield ranking chart template."""

from __future__ import annotations

from datetime import date
from pathlib import Path


def render(as_of: date | str | None = None, variant: str | None = None) -> Path:
    """Render T4 through the requested cutoff date and return the PNG path."""
    raise NotImplementedError("T4 real-yield ranking rendering is not implemented yet.")
