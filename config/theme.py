"""Global visual theme constants for all crypto chart rendering."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"

CANVAS = {
    "width": 1200,
    "height": 675,
    "dpi": 150,
    "background": "#0A0E1A",
}

COLORS = {
    "background": "#0A0E1A",
    "surface": "#0D1426",
    "primary": "#4FC3F7",
    "accent": "#FFD166",
    "up": "#4FC3F7",
    "down": "#EF5350",
    "grid": "#111D35",
    "text_primary": "#E8F0FF",
    "text_muted": "#6B84B8",
    "text_hint": "#2E3F6B",
    "ma7": "#AB47BC",
    "ma30": "#F7931A",
}

TYPOGRAPHY = {
    "font_family": "DejaVu Sans",
    "title": {"size": 22, "weight": "bold"},
    "subtitle": {"size": 11, "weight": "normal"},
    "callout": {"size": 26, "weight": "bold"},
    "annotation": {"size": 9, "weight": "regular"},
    "axis": {"size": 9, "weight": "regular"},
    "watermark": {"size": 10, "weight": "bold"},
}

LAYOUT = {
    "title_x": 0.06,
    "title_y": 0.96,
    "subtitle_y": 0.875,
    "source_x": 0.06,
    "source_y": 0.04,
    "watermark_x": 0.96,
    "watermark_y": 0.04,
    "price_axes": [0.08, 0.28, 0.62, 0.52],
    "volume_axes": [0.08, 0.14, 0.62, 0.10],
    "callout_default": [0.72, 0.82],
    "pct_default": [0.72, 0.725],
}

STYLE = {
    "line_width": 2.4,
    "marker_size": 36,
    "marker_zorder": 3,
    "annotation_offset_points": 12,
    "event_line_width": 1.0,
    "grid_line_width": 0.8,
    "volume_tick_line_width": 0.5,
    "fill_alpha": 0.12,
    "fill_steps": 24,
    "fill_line_width": 0,
    "bar_alpha": 0.72,
    "bar_width": 0.8,
    "spine_width": 0.8,
    "callout_label_gap": 0.155,
    "high_annotation_offset": (0, 12),
    "low_annotation_offset": (28, 10),
}

AXES = {
    "date_format": "%m/%d",
    "max_date_ticks": 8,
    "volume_tick_weekday": 0,
    "volume_right_skip_days": 5,
    "volume_date_label_size": 8,
    "volume_unit_divisor": 1_000_000_000,
    "volume_unit_suffix": "B",
    "volume_decimals": 0,
    "volume_ticks": [0, 50_000_000_000],
    "right_padding_days": 0.5,
}

WATERMARK = {
    "text": "@YourHandle",
    "position": (LAYOUT["watermark_x"], LAYOUT["watermark_y"]),
    "ha": "right",
    "va": "bottom",
}

DATA_RULES = {
    "market_history_frequency": "D",
    "daily_duplicate_aggregation": {
        "price": "last",
        "volume": "last",
    },
}

RENDERING_RULES = {
    "export_contract": "Always save 1200x675 PNG at 150 DPI.",
    "theme_only": "Charts and components must read colors, typography, spacing, and axis rules from config/theme.py.",
    "text_spacing": "Keep title, subtitle, callout, pct change, and labels on separate reserved rows to avoid overlap.",
    "callout_bounds": "Right-side callout text starts at LAYOUT['callout_default'][0] and must remain inside WATERMARK x <= 0.96.",
    "data_frequency": "Collapse intraday duplicate market rows into one daily row before rendering bars or lines.",
    "x_axis_padding": "Price and volume axes share xlim, with right edge padded by AXES['right_padding_days'].",
    "volume_axis": "Volume uses daily bars, no grid, fixed AXES['volume_ticks'], and billion-dollar labels.",
    "date_ticks": "Volume dates show weekly Monday ticks and skip labels near the right edge.",
}
