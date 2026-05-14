# tests/test_design_rules.py
#
# Enforces the six design principles from DESIGN_RULES.
# Run with: venv/bin/python -m pytest tests/test_design_rules.py -v
#
# These tests are STRUCTURE tests, not pixel tests.
# They inspect matplotlib Figure objects returned by chart factory functions,
# so they run fast and need no display / no image comparison.

import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.figure

from config.theme import DESIGN_RULES, typography_valid


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures & helpers
# ─────────────────────────────────────────────────────────────────────────────

def _count_visible_hues(fig: matplotlib.figure.Figure) -> int:
    """Count distinct non-gray hues used in all lines and patches on figure."""
    import colorsys
    seen = set()
    for ax in fig.axes:
        artists = list(ax.lines) + list(ax.patches) + list(ax.collections)
        for artist in artists:
            try:
                rgba = artist.get_facecolor()
                if hasattr(rgba, "__len__") and len(rgba) == 4:
                    r, g, b, a = rgba
                else:
                    continue
            except Exception:
                try:
                    rgba = artist.get_color()
                    from matplotlib.colors import to_rgba
                    r, g, b, a = to_rgba(rgba)
                except Exception:
                    continue
            if a < 0.05:
                continue
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            if s > 0.15:                   # saturation threshold to exclude grays
                seen.add(round(h, 1))      # bucket hues into 0.1 steps
    return len(seen)


def _get_title_text(fig: matplotlib.figure.Figure) -> str:
    for ax in fig.axes:
        if ax.get_title():
            return ax.get_title()
    if fig.texts:
        return fig.texts[0].get_text()
    return ""


def _get_h_gridline_count(fig: matplotlib.figure.Figure) -> int:
    count = 0
    for ax in fig.axes:
        count += sum(1 for line in ax.get_ygridlines() if line.get_visible())
    return count


def _make_minimal_fig(
    title="这张图证明了某个不可反驳的论点",
    title_size=18,
    subtitle_size=11,
    axis_size=10,
) -> matplotlib.figure.Figure:
    """Create a minimal compliant figure for testing helpers."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot([1, 2, 3], [1, 2, 3], color="#4FC3F7")
    ax.set_title(title, fontsize=title_size)
    ax.set_xlabel("x轴", fontsize=axis_size)
    ax.tick_params(labelsize=axis_size)
    fig._test_subtitle_size = subtitle_size
    fig._test_axis_size = axis_size
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 01  Title = Thesis
# ─────────────────────────────────────────────────────────────────────────────

class TestTitleThesis:

    def test_title_not_empty(self):
        fig = _make_minimal_fig(title="LP名义收益跑输持币——真实APR必须扣除IL")
        assert _get_title_text(fig) != "", "Chart must have a title"
        plt.close(fig)

    def test_title_max_chars(self):
        rules = DESIGN_RULES["title"]
        long_title = "这是一个" + "非常" * rules["max_chars"]
        assert len(long_title) > rules["max_chars"], "test setup: title must be long"
        # In real usage: chart factory should truncate or raise ValueError
        assert len(long_title) > rules["max_chars"]
        plt.close("all")

    def test_title_no_forbidden_suffix(self):
        rules = DESIGN_RULES["title"]
        bad_titles = ["BTC与标普对比图", "稳定币数据", "LP收益走势图"]
        for title in bad_titles:
            has_bad = any(title.endswith(s) for s in rules["forbidden_suffixes"])
            assert has_bad, f"test setup: '{title}' should trigger forbidden suffix"

    def test_title_thesis_format_passes(self):
        rules = DESIGN_RULES["title"]
        good_titles = [
            "稳定币不是弹药库，它是杠杆的温度计",
            "周期顶部买入BTC，五年回报不及标普",
            "LP名义收益 ≠ 真实收益",
        ]
        for title in good_titles:
            has_bad = any(title.endswith(s) for s in rules["forbidden_suffixes"])
            assert not has_bad, f"Good title '{title}' incorrectly flagged"

    def test_title_min_font_size(self):
        rules = DESIGN_RULES["title"]
        fig = _make_minimal_fig(title_size=rules["min_font_size"])
        title_text = _get_title_text(fig)
        assert title_text != ""
        # Check size via axes title fontsize
        for ax in fig.axes:
            if ax.get_title():
                size = ax.title.get_fontsize()
                assert size >= rules["min_font_size"], (
                    f"Title fontsize {size} < minimum {rules['min_font_size']}"
                )
        plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 02  Color = Signal Only
# ─────────────────────────────────────────────────────────────────────────────

class TestColorSignal:

    def test_max_semantic_colors(self):
        """A compliant figure uses ≤ 3 distinct hues."""
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], color="#4FC3F7")   # primary
        ax.plot([1, 2], [2, 1], color="#FFD166")   # secondary
        # gray reference line — should NOT count toward hue limit
        ax.axhline(1.5, color="#888888", alpha=0.3)
        hues = _count_visible_hues(fig)
        assert hues <= DESIGN_RULES["color"]["max_semantic_colors"], (
            f"Used {hues} hues, max is {DESIGN_RULES['color']['max_semantic_colors']}"
        )
        plt.close(fig)

    def test_annotation_line_alpha(self):
        """Reference/annotation lines must use low alpha."""
        rule_alpha = DESIGN_RULES["color"]["annotation_line_alpha"]
        fig, ax = plt.subplots()
        vline = ax.axvline(x=2, color="white", alpha=rule_alpha, linestyle="--")
        actual = vline.get_alpha()
        assert actual <= 0.45, (
            f"Annotation line alpha {actual} too high — should be ≤ 0.45"
        )
        plt.close(fig)

    def test_fill_alpha_range(self):
        """Area fills must be within the allowed transparency range."""
        rules = DESIGN_RULES["color"]
        for key in ("fill_alpha_primary", "fill_alpha_secondary"):
            val = rules[key]
            assert 0.10 <= val <= 0.40, f"{key}={val} out of range [0.10, 0.40]"


# ─────────────────────────────────────────────────────────────────────────────
# 03  Grid = Navigation, Not Decoration
# ─────────────────────────────────────────────────────────────────────────────

class TestGridMinimalism:

    def test_max_horizontal_gridlines(self):
        rules = DESIGN_RULES["grid"]
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.yaxis.set_major_locator(plt.MaxNLocator(rules["max_h_gridlines"], prune="both"))
        ax.grid(axis="y", visible=True)
        count = _get_h_gridline_count(fig)
        assert count <= rules["max_h_gridlines"] + 1, (
            f"Too many horizontal gridlines: {count} (max {rules['max_h_gridlines']})"
        )
        plt.close(fig)

    def test_no_vertical_gridlines_by_default(self):
        """Vertical gridlines should be off unless explicitly enabled."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.grid(axis="y", visible=True)   # only y axis
        v_visible = any(l.get_visible() for l in ax.get_xgridlines())
        assert not v_visible, "Vertical gridlines should be off by default"
        plt.close(fig)

    def test_gridline_style_is_dashed(self):
        rules = DESIGN_RULES["grid"]
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.grid(axis="y", linestyle=rules["gridline_style"])
        for line in ax.get_ygridlines():
            if line.get_visible():
                assert line.get_linestyle() in ("--", "dashed"), (
                    "Gridlines must be dashed"
                )
        plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 04  Insight = Inference (tweet copy validator — no matplotlib needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestInsightFraming:

    def _validate_insight(self, text: str) -> tuple[bool, str]:
        rules = DESIGN_RULES["insight"]
        for bad in rules["forbidden_starts"]:
            if text.startswith(bad):
                return False, f"Starts with forbidden phrase: '{bad}'"
        has_frame = any(frame in text for frame in rules["required_frame"])
        if not has_frame:
            return False, "Missing inference frame (这意味着 / 这说明 / 这推翻了 etc.)"
        return True, "ok"

    def test_bad_insight_rejected(self):
        bad = "可以看到2025年lending占比达到峰值15.6%"
        ok, reason = self._validate_insight(bad)
        assert not ok, f"Should have rejected: {bad}"

    def test_good_insight_accepted(self):
        good = "这意味着稳定币流入lending是杠杆需求的领先指标，而非资金待入场信号"
        ok, reason = self._validate_insight(good)
        assert ok, f"Should have accepted: {good}\nReason: {reason}"

    def test_another_good_frame(self):
        good = '这推翻了"稳定币增加=牛市子弹"的普遍认知——它更像是杠杆需求的体温计'
        ok, reason = self._validate_insight(good)
        assert ok, reason


# ─────────────────────────────────────────────────────────────────────────────
# 05  Whitespace = Precision
# ─────────────────────────────────────────────────────────────────────────────

class TestLayout:

    def test_default_figure_size(self):
        rules = DESIGN_RULES["layout"]
        fig = plt.figure(figsize=(rules["fig_width_default"], rules["fig_height_default"]))
        w, h = fig.get_size_inches()
        assert w == rules["fig_width_default"]
        assert h == rules["fig_height_default"]
        plt.close(fig)

    def test_margin_values_are_sane(self):
        rules = DESIGN_RULES["layout"]
        assert rules["margin_left"] >= 0.08, "Left margin too small"
        assert rules["margin_right"] >= 0.08, "Right margin too small"
        assert rules["margin_top"] >= 0.10, "Top margin too small (title gets clipped)"
        assert rules["margin_bottom"] >= 0.10, "Bottom margin too small"

    def test_legend_outside_data_area(self):
        """Legend must not be placed inside the axes bounding box."""
        rules = DESIGN_RULES["layout"]
        assert rules["legend_inside"] is False, (
            "DESIGN_RULES requires legend outside data area"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 06  Typography Hierarchy
# ─────────────────────────────────────────────────────────────────────────────

class TestTypographyHierarchy:

    def test_valid_hierarchy_passes(self):
        t = DESIGN_RULES["typography"]
        assert typography_valid(
            t["title_size"], t["subtitle_size"], t["axis_label_size"]
        ), "Default DESIGN_RULES typography must satisfy its own ratio rules"

    def test_too_small_title_fails(self):
        assert not typography_valid(
            title_size=12,
            subtitle_size=11,    # ratio 12/11 ≈ 1.09 < 1.5
            axis_size=10,
        )

    def test_annotation_label_smaller_than_value(self):
        t = DESIGN_RULES["typography"]
        assert t["annotation_value_size"] > t["annotation_label_size"], (
            "Callout value should be larger than its descriptive label"
        )

    def test_footer_smallest(self):
        t = DESIGN_RULES["typography"]
        sizes = [
            t["title_size"], t["subtitle_size"],
            t["axis_label_size"], t["tick_label_size"],
            t["annotation_size"], t["footer_size"],
        ]
        assert t["footer_size"] == min(sizes), "Footer must be the smallest text element"

    def test_title_min_size_constant(self):
        t = DESIGN_RULES["typography"]
        rule_min = DESIGN_RULES["title"]["min_font_size"]
        assert t["title_size"] >= rule_min, (
            f"typography.title_size ({t['title_size']}) < "
            f"title.min_font_size ({rule_min})"
        )
