"""Chart template registry for scheduled crypto publishing assets."""

from __future__ import annotations

from importlib import import_module
import inspect
from pathlib import Path

from config.templates import TEMPLATES, get_template_config


def render_template(
    template_id: str,
    as_of: str | None = None,
    variant: str | None = None,
    insight_text: str | None = None,
    title: str | None = None,
) -> Path:
    """Render one template by id using its centralized metadata registry entry."""
    config = get_template_config(template_id)
    module = import_module(config.module)
    kwargs = {"as_of": as_of, "variant": variant}
    if "insight_text" in inspect.signature(module.render).parameters:
        kwargs["insight_text"] = insight_text
    if "title" in inspect.signature(module.render).parameters:
        kwargs["title"] = title
    return module.render(**kwargs)


__all__ = ["TEMPLATES", "get_template_config", "render_template"]
