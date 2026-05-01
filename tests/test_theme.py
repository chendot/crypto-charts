"""Unit tests for global chart theme constants."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import theme


HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_required_theme_fields_exist() -> None:
    """Verify all required top-level theme fields and color keys exist."""
    assert hasattr(theme, "CANVAS")
    assert hasattr(theme, "COLORS")
    assert hasattr(theme, "TYPOGRAPHY")
    assert hasattr(theme, "LAYOUT")
    assert hasattr(theme, "WATERMARK")

    for key in (
        "background",
        "surface",
        "primary",
        "accent",
        "up",
        "down",
        "grid",
        "text_primary",
        "text_muted",
        "text_hint",
        "ma7",
        "ma30",
    ):
        assert key in theme.COLORS


def test_colors_are_valid_hex() -> None:
    """Verify all theme colors use legal six-digit hex values."""
    for color in theme.COLORS.values():
        assert HEX_RE.match(color)
    assert HEX_RE.match(theme.CANVAS["background"])


def test_canvas_size_matches_x_platform_ratio() -> None:
    """Verify the canvas is the configured 16:9 X-friendly image size."""
    assert theme.CANVAS["width"] == 1200
    assert theme.CANVAS["height"] == 675
    assert theme.CANVAS["width"] / theme.CANVAS["height"] == 16 / 9


if __name__ == "__main__":
    test_required_theme_fields_exist()
    test_colors_are_valid_hex()
    test_canvas_size_matches_x_platform_ratio()
    print("All theme tests passed.")
