"""Global visual theme constants for all crypto chart rendering.

Color organization:
    - base:           Background, surface, grid (chart canvas foundation)
    - text:           All text colors (title, body, muted, footer)
    - data:           Generic data series colors (primary/accent/tertiary/quaternary/diff)
    - series:         Business-semantic colors (MA lines, technical indicators)
    - etf:            ETF-specific fund colors
    - content_series: Content series identifier colors (system A=LP, B=Yield, E=Risk)
                      USAGE LIMIT: only for series label text, title side-bar, key
                      number emphasis. NEVER enters data visualization body.
"""

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
    # ---- Canvas foundation ----
    "base": {
        "background": "#0A0E1A",
        "surface": "#0D1426",
        "grid": "#111D35",
    },

    # ---- Text colors ----
    "text": {
        "primary": "#E8F0FF",
        "muted": "#6B84B8",
        "hint": "#2E3F6B",
        "label_muted": "#6B7280",
        "footer": "#6B7280",          # Used by @koalada18 watermark
    },

    # ---- Generic data series colors ----
    # Use these as default palette for any new chart unless business semantics require otherwise.
    "data": {
        "primary": "#4FC3F7",         # Ice blue (main series)
        "accent": "#FFD166",           # Warm gold (secondary series)
        "tertiary": "#A8FF78",         # Lime (third comparison)
        "quaternary": "#A78BFA",       # Violet (fourth comparison / correlation)
        "up": "#4FC3F7",
        "down": "#EF5350",
        "diff": "#475569",             # Difference / eroded portion (Series A specifically)
        "mint": "#00C896",
        "rose": "#FF6B6B",
    },

    # ---- Business-semantic colors ----
    # Reserved for specific technical indicators or recurring chart types.
    "series": {
        "ma7": "#AB47BC",
        "ma30": "#F7931A",
    },

    # ---- ETF-specific fund colors ----
    "etf": {
        "ibit": "#4FC3F7",
        "fbtc": "#A8FF78",
        "bitb": "#FFD166",
        "arkb": "#A78BFA",
        "gbtc": "#EF5350",
        "others": "#6B84B8",
        "cumulative": "#E8F0FF",
    },

    # ---- Content series identifier colors ----
    # USAGE: series label text only, optional 2px title side-bar, at most 1 key
    # number per chart. MUST NOT enter data visualization body.
    # Series C / D / F have no auxiliary color (text-only label in text.muted).
    "content_series": {
        "A_lp": "#C4A8FF",             # LP yield illusion (light violet, avoids etf.arkb collision)
        "B_yield": "#F4A261",          # Yield decomposition (warm amber)
        "E_risk": "#E76F51",           # Risk structure (warning coral)
    },
}

TYPOGRAPHY = {
    "font_family": "DejaVu Sans",
    "font_family_mono": "Menlo",      # Monospace for footer @koalada18 (fallback: JetBrains Mono, IBM Plex Mono)
    "title": {"size": 22, "weight": "bold"},
    "subtitle": {"size": 11, "weight": "normal"},
    "callout": {"size": 26, "weight": "bold"},
    "annotation": {"size": 9, "weight": "regular"},
    "axis": {"size": 9, "weight": "regular"},
    "watermark": {"size": 10, "weight": "bold"},
    "series_label": {"size": 11, "weight": "regular"},   # Content series identifier under title
    "footer": {"size": 10, "weight": "regular"},          # @koalada18 footer
    "method_note": {"size": 10, "weight": "regular"},     # Method: ... in subtitle
}

LAYOUT = {
    "title_x": 0.06,
    "title_y": 0.96,
    "subtitle_y": 0.875,
    "series_label_y": 0.825,           # Content series identifier (below subtitle)
    "source_x": 0.06,
    "source_y": 0.04,
    "watermark_x": 0.96,
    "watermark_y": 0.04,
    "footer_x": 0.5,                   # @koalada18 footer (centered)
    "footer_y": 0.02,
    "price_axes": [0.08, 0.28, 0.62, 0.52],
    "volume_axes": [0.08, 0.14, 0.62, 0.10],
    "callout_default": [0.72, 0.82],
    "pct_default": [0.72, 0.725],
    "macro_title_x": 0.08,
    "macro_title_y": 0.96,
    "macro_subtitle_y": 0.885,
    "macro_series_label_y": 0.835,
    "macro_source_x": 0.08,
    "macro_source_y": 0.02,
    "macro_watermark_x": 0.96,
    "macro_watermark_y": 0.02,
    "macro_axes": [0.08, 0.15, 0.74, 0.66],
    "macro_callout_center": [0.89, 0.72],
    "correlation_axes": [0.08, 0.34, 0.72, 0.47],
    "correlation_btc_axes": [0.08, 0.13, 0.72, 0.17],
    "correlation_callout": [0.84, 0.72],
    "etf_axes": [0.08, 0.20, 0.66, 0.58],
    "etf_callout": [0.78, 0.80],
    "etf_insight_box": [0.08, 0.08],   # Deprecated: insight box permanently removed
    "t6_axes": [0.10, 0.19, 0.68, 0.58],
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
    "etf_bar_width": 0.12,
    "etf_bar_alpha": 0.92,
    "etf_cumulative_line_width": 2.0,
    "etf_cumulative_marker_size": 28,
    "etf_zero_line_width": 1.0,
    "etf_insight_box_alpha": 0.82,    # Deprecated: insight box removed
    "etf_insight_box_pad": 0.45,       # Deprecated: insight box removed
    "bump_label_min_gap": 0.4,
    "bump_label_offset_x": 0.34,
    "bump_arrow_offset_x": 0.82,
    "title_sidebar_width": 2,          # Optional 2px title side-bar (content series A/B/E)
    "title_sidebar_height_ratio": 0.6, # Side-bar height as fraction of title font size
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

WATERMARK_HANDLE = "@koalada18"

WATERMARK = {
    "text": WATERMARK_HANDLE,
    "position": (LAYOUT["watermark_x"], LAYOUT["watermark_y"]),
    "ha": "right",
    "va": "bottom",
}

FOOTER = {
    "text": WATERMARK_HANDLE,
    "position": (LAYOUT["footer_x"], LAYOUT["footer_y"]),
    "ha": "center",
    "va": "bottom",
    "color": COLORS["text"]["footer"],
    "fontfamily": TYPOGRAPHY["font_family_mono"],
    "fontsize": TYPOGRAPHY["footer"]["size"],
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
    "text_spacing": "Keep title, subtitle, series_label, callout, pct change, and labels on separate reserved rows to avoid overlap.",
    "callout_bounds": "Right-side callout text starts at LAYOUT['callout_default'][0] and must remain inside WATERMARK x <= 0.96.",
    "data_frequency": "Collapse intraday duplicate market rows into one daily row before rendering bars or lines.",
    "x_axis_padding": "Price and volume axes share xlim, with right edge padded by AXES['right_padding_days'].",
    "volume_axis": "Volume uses daily bars, no grid, fixed AXES['volume_ticks'], and billion-dollar labels.",
    "date_ticks": "Volume dates show weekly Monday ticks and skip labels near the right edge.",
    "method_required": "From Series A onward, subtitle MUST include 'Method: ...' segment after Source and Period.",
    "content_series_color": "content_series colors are for series identifier label, optional title side-bar, and at most ONE key number per chart. NEVER use them for data lines/bars/areas.",
    "footer_handle": "Every chart MUST render @koalada18 footer in monospace at LAYOUT['footer_x/y'].",
}

CONTENT_SERIES = {
    "A_lp": {
        "label": "LP 收益幻觉",
        "color": COLORS["content_series"]["A_lp"],
        "use_color": True,
    },
    "B_yield": {
        "label": "收益率拆解",
        "color": COLORS["content_series"]["B_yield"],
        "use_color": True,
    },
    "C_token": {
        "label": "代币激励的真实账",
        "color": COLORS["text"]["muted"],
        "use_color": False,
    },
    "D_narrative": {
        "label": "DeFi 叙事周期",
        "color": COLORS["text"]["muted"],
        "use_color": False,
    },
    "E_risk": {
        "label": "DeFi 风险结构",
        "color": COLORS["content_series"]["E_risk"],
        "use_color": True,
    },
    "F_ranking": {
        "label": "榜单幻觉",
        "color": COLORS["text"]["muted"],
        "use_color": False,
    },
    "X_macro": {
        "label": "宏观参照",
        "color": COLORS["text"]["muted"],
        "use_color": False,
    },
}

ETF_FLOW = {
    "featured_funds": ("IBIT", "FBTC", "BITB", "ARKB", "GBTC"),
    "category_order": ("IBIT", "FBTC", "BITB", "ARKB", "GBTC", "Others"),
    "colors": {
        "IBIT": COLORS["etf"]["ibit"],
        "FBTC": COLORS["etf"]["fbtc"],
        "BITB": COLORS["etf"]["bitb"],
        "ARKB": COLORS["etf"]["arkb"],
        "GBTC": COLORS["etf"]["gbtc"],
        "Others": COLORS["etf"]["others"],
    },
    "source": "Source: Farside Investors",
    "flow_unit_divisor": 1_000_000,
    "flow_unit_suffix": "M",
    "cumulative_unit_divisor": 1_000_000,
    "cumulative_unit_suffix": "M",
}
