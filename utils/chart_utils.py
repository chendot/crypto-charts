"""Reusable chart helpers for crypto-charts.

All visual parameters are sourced from config/theme.py.
No hardcoded colors, sizes, or alpha values in this module.

Public API
----------
apply_dual_axis_colors(ax_left, ax_right, color_left, color_right)
    Bind each axis's tick/label color to its data series color.

add_callout(ax, x, y, label, value_text, *, vline=True, side="left", vline_alpha=None)
    Standardized annotated callout: vertical reference line + value + label.

add_series_label(fig, series_key)
    Render content series identifier below subtitle per LAYOUT["series_label_y"].

apply_grid(ax)
    Apply Rule 03 grid settings from DESIGN_RULES["grid"].

apply_legend(ax, **kwargs)
    Place legend outside data area per Rule 05.

validate_title(title)
    Raise ValueError if title violates Rule 01 constraints.

validate_tweet_copy(text)
    Raise ValueError if tweet copy violates Rule 04 framing constraints.
"""

from __future__ import annotations

import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from config.theme import COLORS, CONTENT_SERIES, DESIGN_RULES, LAYOUT, STYLE, TYPOGRAPHY


# ── Internal shortcuts (never re-exported) ───────────────────────────────────

_C = DESIGN_RULES["color"]
_G = DESIGN_RULES["grid"]
_T = DESIGN_RULES["typography"]
_DX = DESIGN_RULES["dual_axis"]


# ─────────────────────────────────────────────────────────────────────────────
# Rule 02 helper — dual-axis color binding
# ─────────────────────────────────────────────────────────────────────────────

def apply_dual_axis_colors(
    ax_left: matplotlib.axes.Axes,
    ax_right: matplotlib.axes.Axes,
    color_left: str,
    color_right: str,
) -> None:
    """Bind each Y-axis tick and label color to its data series color.

    Required for every dual-axis chart (Series D and X_macro exceptions).
    Implements DESIGN_RULES["dual_axis"]["enforce_color_binding"].

    Parameters
    ----------
    ax_left:     The primary (left) Axes object.
    ax_right:    The secondary (right) Axes object (twinx).
    color_left:  Hex color string matching the left data series.
    color_right: Hex color string matching the right data series.
    """
    right_alpha = _DX["right_axis_label_alpha"]

    for ax, color, alpha in (
        (ax_left, color_left, 1.0),
        (ax_right, color_right, right_alpha),
    ):
        ax.yaxis.label.set_color(color)
        ax.tick_params(axis="y", colors=color, labelsize=_T["tick_label_size"])
        for spine in ax.spines.values():
            spine.set_visible(False)
        for tick in ax.yaxis.get_major_ticks():
            tick.label1.set_alpha(alpha)
            tick.label2.set_alpha(alpha)


# ─────────────────────────────────────────────────────────────────────────────
# Rule 03 helper — grid
# ─────────────────────────────────────────────────────────────────────────────

def apply_grid(ax: matplotlib.axes.Axes) -> None:
    """Apply Rule 03 grid settings.

    - Horizontal dashed lines only, max DESIGN_RULES["grid"]["max_h_gridlines"].
    - Vertical gridlines off.
    - Style and linewidth from DESIGN_RULES["grid"].
    """
    ax.yaxis.set_major_locator(
        mticker.MaxNLocator(_G["max_h_gridlines"], prune="both")
    )
    ax.grid(
        axis="y",
        linestyle=_G["gridline_style"],
        linewidth=_G["gridline_linewidth"],
        color=COLORS["base"]["grid"],
        alpha=_C["gridline_alpha"],
    )
    ax.grid(axis="x", visible=False)


# ─────────────────────────────────────────────────────────────────────────────
# Rule 02 + 06 helper — standardized callout annotation
# ─────────────────────────────────────────────────────────────────────────────

def add_callout(
    ax: matplotlib.axes.Axes,
    x,
    y: float,
    label: str,
    value_text: str,
    *,
    vline: bool = True,
    side: str = "left",
    vline_alpha: float | None = None,
    label_color: str | None = None,
    value_color: str | None = None,
) -> None:
    """Add a standardized annotated callout to a chart.

    Renders: optional vertical reference line + value text (larger) + label text (smaller).
    Typography sizes sourced from DESIGN_RULES["typography"].

    Parameters
    ----------
    ax:           Target Axes.
    x:            X-position (datetime or numeric) for the callout.
    y:            Y-position for the callout text anchor.
    label:        Descriptive label (e.g. "牛市顶部"). Rendered at annotation_label_size.
    value_text:   Key number or value (e.g. "15.6%"). Rendered at annotation_value_size.
    vline:        Whether to draw a vertical reference line at x.
    side:         "left" or "right" — which side to offset label text.
    vline_alpha:  Override alpha for vline; defaults to DESIGN_RULES["color"]["annotation_line_alpha"].
    label_color:  Override color for label text; defaults to COLORS["text"]["muted"].
    value_color:  Override color for value text; defaults to COLORS["text"]["primary"].
    """
    alpha = vline_alpha if vline_alpha is not None else _C["annotation_line_alpha"]
    lc = label_color or COLORS["text"]["muted"]
    vc = value_color or COLORS["text"]["primary"]
    offset_pts = STYLE["annotation_offset_points"]
    ha = "left" if side == "right" else "right"
    x_offset = offset_pts if side == "right" else -offset_pts

    if vline:
        ax.axvline(
            x=x,
            color=COLORS["text"]["hint"],
            linewidth=STYLE["event_line_width"],
            linestyle="--",
            alpha=alpha,
            zorder=1,
        )

    ax.annotate(
        value_text,
        xy=(x, y),
        xytext=(x_offset, 4),
        textcoords="offset points",
        ha=ha,
        va="bottom",
        fontsize=_T["annotation_value_size"],
        color=vc,
        fontweight="bold",
    )
    ax.annotate(
        label,
        xy=(x, y),
        xytext=(x_offset, -10),
        textcoords="offset points",
        ha=ha,
        va="top",
        fontsize=_T["annotation_label_size"],
        color=lc,
        alpha=0.85,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Content series label renderer
# ─────────────────────────────────────────────────────────────────────────────

def add_series_label(
    fig: matplotlib.figure.Figure,
    series_key: str,
) -> None:
    """Render the content series identifier below subtitle.

    Position: LAYOUT["series_label_y"], left-aligned at LAYOUT["title_x"].
    Color: CONTENT_SERIES[series_key]["color"] when use_color=True, else text.muted.

    Parameters
    ----------
    fig:        The Figure object.
    series_key: One of the CONTENT_SERIES keys (e.g. "A_lp", "B_yield").

    Raises
    ------
    KeyError if series_key is not in CONTENT_SERIES.
    """
    series = CONTENT_SERIES[series_key]
    color = series["color"]  # already resolves to text.muted for no-color series
    fig.text(
        LAYOUT["title_x"],
        LAYOUT["series_label_y"],
        series["label"],
        ha="left",
        va="top",
        fontsize=TYPOGRAPHY["series_label"]["size"],
        fontweight=TYPOGRAPHY["series_label"]["weight"],
        color=color,
        transform=fig.transFigure,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Optional title side-bar (Series A / B / E only)
# ─────────────────────────────────────────────────────────────────────────────

def add_title_sidebar(
    fig: matplotlib.figure.Figure,
    series_key: str,
    title_fontsize: int | None = None,
) -> None:
    """Draw the optional 2px vertical color bar immediately left of the title.

    Only meaningful for Series A, B, E (use_color=True).
    Safe no-op for other series.

    Parameters
    ----------
    fig:           The Figure object.
    series_key:    Content series key.
    title_fontsize: Actual title font size; defaults to TYPOGRAPHY["title"]["size"].
    """
    series = CONTENT_SERIES[series_key]
    if not series["use_color"]:
        return

    fs = title_fontsize or TYPOGRAPHY["title"]["size"]
    bar_height = STYLE["title_sidebar_height_ratio"] * fs / (CANVAS_HEIGHT_PT := 675)
    bar_x = LAYOUT["title_x"] - 0.012
    bar_y = LAYOUT["title_y"] - bar_height

    fig.add_axes(
        [bar_x, bar_y, STYLE["title_sidebar_width"] / 1200, bar_height],
        label=f"_sidebar_{series_key}",
    ).set_facecolor(series["color"])

    for spine in fig.axes[-1].spines.values():
        spine.set_visible(False)
    fig.axes[-1].set_xticks([])
    fig.axes[-1].set_yticks([])


# ─────────────────────────────────────────────────────────────────────────────
# Rule 05 helper — legend placement
# ─────────────────────────────────────────────────────────────────────────────

def apply_legend(
    ax: matplotlib.axes.Axes,
    *,
    loc: str = "upper left",
    bbox_to_anchor: tuple = (0.01, 0.99),
    **kwargs,
) -> matplotlib.legend.Legend:
    """Place legend outside data area per Rule 05.

    Always sets frameon=False and uses COLORS["text"]["muted"] for text.
    Passes any extra kwargs to ax.legend().

    Returns the Legend object.
    """
    legend = ax.legend(
        loc=loc,
        bbox_to_anchor=bbox_to_anchor,
        borderaxespad=0,
        frameon=False,
        labelcolor=COLORS["text"]["muted"],
        fontsize=_T["annotation_label_size"],
        **kwargs,
    )
    return legend


# ─────────────────────────────────────────────────────────────────────────────
# Rule 01 validator — title
# ─────────────────────────────────────────────────────────────────────────────

def validate_title(title: str) -> None:
    """Raise ValueError if the title violates Rule 01.

    Checks:
    - Not empty.
    - Length <= DESIGN_RULES["title"]["max_chars"].
    - Does not end with a forbidden suffix (descriptive, not thesis).

    Parameters
    ----------
    title: The chart title string.

    Raises
    ------
    ValueError with a descriptive message on first violation.
    """
    rules = DESIGN_RULES["title"]

    if not title or not title.strip():
        raise ValueError("Title must not be empty.")

    if len(title) > rules["max_chars"]:
        raise ValueError(
            f"Title too long: {len(title)} chars (max {rules['max_chars']}). "
            "Long titles are usually descriptions, not theses."
        )

    for suffix in rules["forbidden_suffixes"]:
        if title.rstrip().endswith(suffix):
            raise ValueError(
                f"Title ends with forbidden suffix '{suffix}'. "
                "Rewrite as a falsifiable claim, not a description."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Rule 04 validator — tweet copy
# ─────────────────────────────────────────────────────────────────────────────

def validate_tweet_copy(text: str) -> None:
    """Raise ValueError if tweet copy violates Rule 04 framing constraints.

    Checks:
    - Does not start with a forbidden recap phrase.
    - Contains at least one required inference frame.

    Parameters
    ----------
    text: The full tweet body text.

    Raises
    ------
    ValueError with a descriptive message on first violation.
    """
    rules = DESIGN_RULES["insight"]

    for bad in rules["forbidden_starts"]:
        if text.lstrip().startswith(bad):
            raise ValueError(
                f"Tweet copy starts with forbidden phrase '{bad}'. "
                "Insight must be inference, not a recap of the chart."
            )

    has_frame = any(frame in text for frame in rules["required_frame"])
    if not has_frame:
        frames = " / ".join(f"「{f}」" for f in rules["required_frame"])
        raise ValueError(
            f"Tweet copy missing inference frame. "
            f"Include at least one of: {frames}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: apply standard macro-chart axis style
# ─────────────────────────────────────────────────────────────────────────────

def style_axes(
    ax: matplotlib.axes.Axes,
    *,
    hide_spines: tuple[str, ...] = ("top", "right", "bottom"),
    left_spine_color: str | None = None,
) -> None:
    """Apply standard axis cosmetics shared across all chart types.

    - Removes top/right/bottom spines by default.
    - Sets tick label size and color from DESIGN_RULES.
    - Applies grid via apply_grid().

    Parameters
    ----------
    ax:               Target Axes.
    hide_spines:      Spine names to hide. Default: top, right, bottom.
    left_spine_color: Color for left spine; defaults to COLORS["base"]["grid"].
    """
    spine_color = left_spine_color or COLORS["base"]["grid"]

    for name, spine in ax.spines.items():
        if name in hide_spines:
            spine.set_visible(False)
        else:
            spine.set_color(spine_color)
            spine.set_linewidth(STYLE["spine_width"])

    ax.tick_params(
        axis="both",
        labelsize=_T["tick_label_size"],
        colors=COLORS["text"]["muted"],
        length=0,
    )
    ax.yaxis.label.set_color(COLORS["text"]["muted"])
    ax.yaxis.label.set_size(_T["axis_label_size"])
    ax.xaxis.label.set_color(COLORS["text"]["muted"])
    ax.xaxis.label.set_size(_T["axis_label_size"])

    apply_grid(ax)
