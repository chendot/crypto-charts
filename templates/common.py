"""Shared helpers for template modules."""

from __future__ import annotations

from datetime import date, datetime


def normalize_as_of(as_of: date | str | None) -> date:
    """Return a concrete cutoff date for a render request."""
    if as_of is None:
        return date.today()
    if isinstance(as_of, date):
        return as_of
    return datetime.strptime(as_of, "%Y-%m-%d").date()


def output_filename(template_id: str, as_of: date | str | None = None, variant: str | None = None) -> str:
    """Build a chart output filename using the project naming convention."""
    cutoff = normalize_as_of(as_of)
    parts = [cutoff.strftime("%Y-%m-%d"), template_id.lower()]
    if variant:
        parts.append(variant.lower().replace(" ", "-"))
    return "_".join(parts) + ".png"
