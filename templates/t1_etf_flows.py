"""Compatibility wrapper for the T1 BTC spot ETF flow template."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from templates.t1_etf_flow import render as _render


def render(
    as_of: date | str | None = None,
    variant: str | None = None,
    title: str | None = None,
) -> Path:
    """Render T1 through the requested cutoff date and return the PNG path."""
    return _render(as_of=as_of, variant=variant, title=title)
