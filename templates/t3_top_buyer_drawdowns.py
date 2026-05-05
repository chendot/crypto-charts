"""T3: Historical top-buyer drawdown comparison chart template."""

from __future__ import annotations

from datetime import date
from pathlib import Path


def render(as_of: date | str | None = None, variant: str | None = None) -> Path:
    """Render T3 for the requested variant and return the PNG path."""
    raise NotImplementedError("T3 top-buyer drawdown rendering is not implemented yet.")
