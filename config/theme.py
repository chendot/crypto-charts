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
        "F_ranking": "#6B84B8",         # Ranking illusion (muted; no auxiliary hue)
    },
}

TYPOGRAPHY = {
    "font_family": "Hiragino Sans GB",
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
        "color": COLORS["content_series"]["F_ranking"],
        "use_color": False,
    },
    "X_macro": {
        "label": "宏观参照",
        "color": COLORS["text"]["muted"],
        "use_color": False,
    },
}

PERP_DEX_SCATTER = {
    "xlim": (20, 250),
    "ylim": (0.1, 12),
    "x_ticks": (20, 40, 60, 100, 180),
    "y_ticks": (0.1, 0.2, 0.5, 1, 2, 5, 10),
    "reference_points": ((20, 0.6), (200, 6.0)),
    "reference_alpha": 0.50,
    "reference_label_offset": (-2, 6),
    "tick_label_zorder": 10,
    "x_tick_label_y": 0.04,
    "x_label_pad": 4,
    "marker_sizes": {
        "featured": 120,
        "default": 80,
    },
    "annotation_offsets": {
        "Hyperliquid": (8, 6),
        "Aster": (8, 0),
        "edgeX": (12, -4),
        "Lighter": (8, 8),
        "Grvt": (-18, -2),
        "ApeX": (8, -18),
    },
    "annotation_line_gap": -10,
    "source_position": (0.06, 0.015),
}

PERP_DEX_RANKING = {
    "xlim": (0, 5.5),
    "bar_height": 0.45,
    "reference_value": 3.17,
    "reference_alpha": 0.40,
    "value_offset": 0.05,
    "rank_change_offset": 0.42,
    "reference_label_offset": (0, -4),
    "reference_label_y_offset": -0.4,
    "top_padding": 0.85,
    "label_name_x": -0.075,
    "label_rank_x": -0.005,
    "break_x": 5.3,
    "break_linewidth": 1.5,
    "break_slash_dx": 0.025,
    "break_slash_dy": 0.10,
    "break_slash_gap": 0.06,
    "hyperliquid_display_value": 5.5,
    "hyperliquid_value_x": 5.58,
    "hyperliquid_rank_change_x": 6.00,
    "hyperliquid_note_x": 5.35,
    "hyperliquid_note_y_offset": -0.36,
    "source_position": PERP_DEX_SCATTER["source_position"],
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

# Design rules derived from Messari / The Block / ARK / Datawrapper analysis
# These are constants, not suggestions. Codex prompts and tests both reference them.

DESIGN_RULES = {

    # ── 01  Title = Thesis ────────────────────────────────────────────────
    # Title must be a falsifiable claim, not a description.
    # Enforced: pytest checks title doesn't end with common non-thesis patterns.
    "title": {
        "min_font_size": 16,        # px — absolute floor for chart title
        "max_chars": 60,            # force brevity; long titles are usually descriptions
        "forbidden_suffixes": [     # titles ending with these are probably descriptions
            "对比图", "分布图", "走势图", "数据", "图表", "overview", "chart",
        ],
    },

    # ── 02  Color = Signal Only ───────────────────────────────────────────
    # Max 3 semantic colors per chart. Everything else is gray-family.
    # Semantic colors are defined in COLORS['series'] and COLORS['data'].
    "color": {
        "max_semantic_colors": 3,   # hard limit of distinct hues in one figure
        "annotation_line_alpha": 0.30,   # vertical/horizontal reference lines
        "fill_alpha_primary": 0.25,      # area fill under primary line
        "fill_alpha_secondary": 0.12,    # area fill under secondary line
        "gridline_alpha": 0.18,          # horizontal grid lines
        "axis_label_alpha": 0.55,        # tick labels, axis titles
    },

    # ── 03  Grid = Navigation, Not Decoration ────────────────────────────
    # Maximum 5 horizontal gridlines. Vertical gridlines: none by default.
    "grid": {
        "max_h_gridlines": 5,
        "v_gridlines_default": False,
        "gridline_style": "--",          # dashed only
        "gridline_linewidth": 0.5,
    },

    # ── 04  Insight = Inference, Not Recap ───────────────────────────────
    # Insight box is removed from chart canvas (per prior decision).
    # This block is kept as a writing checklist constant for tweet copy generation.
    "insight": {
        "forbidden_starts": [       # tweet body / caption must NOT start with these
            "可以看到", "图表显示", "数据表明", "从图中", "如图所示",
        ],
        "required_frame": [         # at least one of these frames should appear
            "这意味着", "这说明", "这推翻了", "这暴露了", "这改变了",
            "意味着", "说明", "推翻了", "暴露了",
        ],
    },

    # ── 05  Whitespace = Precision ────────────────────────────────────────
    # Data area should occupy ~65% of canvas. Margins enforced in inches (matplotlib).
    "layout": {
        "fig_width_default": 12,         # inches
        "fig_height_default": 6,         # inches — 2:1 ratio for Twitter
        "margin_left": 0.10,             # fraction of figure width
        "margin_right": 0.10,
        "margin_top": 0.14,              # headroom for title + subtitle
        "margin_bottom": 0.12,
        "data_area_target": 0.65,        # ideal fraction of canvas used by data
        "legend_inside": False,          # legend always outside data area
    },

    # ── 06  Typography Hierarchy ──────────────────────────────────────────
    # Minimum ratio between adjacent hierarchy levels.
    # e.g., title must be >= 1.5x subtitle font size.
    "typography": {
        "title_size": 18,           # pt
        "subtitle_size": 11,        # pt  (ratio ≥ 1.5x enforced by test)
        "axis_label_size": 10,      # pt
        "tick_label_size": 9,       # pt
        "annotation_size": 9,       # pt  (callout text on chart)
        "footer_size": 8,           # pt
        "min_title_subtitle_ratio": 1.5,   # test enforces title/subtitle >= this
        "min_subtitle_axis_ratio": 1.1,    # test enforces subtitle/axis >= this
        "annotation_value_size": 11,       # larger: the number at callout point
        "annotation_label_size": 8,        # smaller: the descriptive label
    },

    # ── Dual-axis specific rules (Series D and exception charts) ──────────
    "dual_axis": {
        # Left axis tick color must match left series color
        # Right axis tick color must match right series color
        # Enforced by: _apply_dual_axis_colors() helper (see chart_utils.py)
        "enforce_color_binding": True,
        "right_axis_label_alpha": 0.80,   # slightly muted vs left
    },
}


# ── Convenience accessors ─────────────────────────────────────────────────────

def get_rule(section: str, key: str):
    """Single-key accessor with a clear KeyError if section/key is wrong."""
    return DESIGN_RULES[section][key]


def typography_valid(title_size: float, subtitle_size: float, axis_size: float) -> bool:
    """Returns True if the three sizes satisfy the hierarchy ratios."""
    t = DESIGN_RULES["typography"]
    return (
        title_size / subtitle_size >= t["min_title_subtitle_ratio"]
        and subtitle_size / axis_size >= t["min_subtitle_axis_ratio"]
    )
