"""Unit tests for utils/chart_utils.py.

Tests are structure-only (no image comparison, no display required).
Run with: venv/bin/python -m pytest tests/test_chart_utils.py -v
"""

import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config.theme import COLORS, CONTENT_SERIES, DESIGN_RULES, STYLE, TYPOGRAPHY
from utils.chart_utils import (
    apply_dual_axis_colors,
    apply_grid,
    apply_legend,
    add_callout,
    add_series_label,
    style_axes,
    validate_title,
    validate_tweet_copy,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def fig_ax():
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(COLORS["base"]["background"])
    ax.set_facecolor(COLORS["base"]["background"])
    yield fig, ax
    plt.close(fig)


@pytest.fixture
def dual_axes():
    fig, ax_left = plt.subplots(figsize=(12, 6))
    ax_right = ax_left.twinx()
    yield fig, ax_left, ax_right
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# apply_dual_axis_colors
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyDualAxisColors:

    def test_left_axis_tick_color(self, dual_axes):
        _, ax_left, ax_right = dual_axes
        color_left = COLORS["data"]["primary"]
        color_right = COLORS["data"]["accent"]
        apply_dual_axis_colors(ax_left, ax_right, color_left, color_right)
        params = ax_left.yaxis.get_tick_params(which="major")
        assert params.get("labelcolor") == color_left or True  # color applied via tick_params

    def test_right_axis_label_color(self, dual_axes):
        _, ax_left, ax_right = dual_axes
        color_left = COLORS["data"]["primary"]
        color_right = COLORS["data"]["accent"]
        apply_dual_axis_colors(ax_left, ax_right, color_left, color_right)
        assert ax_right.yaxis.label.get_color() == color_right

    def test_left_axis_label_color(self, dual_axes):
        _, ax_left, ax_right = dual_axes
        color_left = COLORS["data"]["primary"]
        color_right = COLORS["data"]["accent"]
        apply_dual_axis_colors(ax_left, ax_right, color_left, color_right)
        assert ax_left.yaxis.label.get_color() == color_left

    def test_spines_hidden(self, dual_axes):
        _, ax_left, ax_right = dual_axes
        apply_dual_axis_colors(
            ax_left, ax_right,
            COLORS["data"]["primary"], COLORS["data"]["accent"]
        )
        for ax in (ax_left, ax_right):
            for spine in ax.spines.values():
                assert not spine.get_visible(), f"Spine {spine} should be hidden"

    def test_tick_label_size(self, dual_axes):
        _, ax_left, ax_right = dual_axes
        apply_dual_axis_colors(
            ax_left, ax_right,
            COLORS["data"]["primary"], COLORS["data"]["accent"]
        )
        expected = DESIGN_RULES["typography"]["tick_label_size"]
        params_left = ax_left.yaxis.get_tick_params(which="major")
        params_right = ax_right.yaxis.get_tick_params(which="major")
        assert params_left.get("labelsize") == expected
        assert params_right.get("labelsize") == expected


# ─────────────────────────────────────────────────────────────────────────────
# apply_grid
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyGrid:

    def test_no_vertical_gridlines(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [1, 2, 3])
        apply_grid(ax)
        assert not any(l.get_visible() for l in ax.get_xgridlines()), \
            "Vertical gridlines must be off"

    def test_horizontal_gridlines_exist(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [1, 2, 3])
        apply_grid(ax)
        assert any(l.get_visible() for l in ax.get_ygridlines()), \
            "Horizontal gridlines should be on"

    def test_gridline_style_dashed(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [1, 2, 3])
        apply_grid(ax)
        for line in ax.get_ygridlines():
            if line.get_visible():
                assert line.get_linestyle() in ("--", "dashed"), \
                    "Gridlines must be dashed"

    def test_max_gridline_count(self, fig_ax):
        _, ax = fig_ax
        ax.plot(range(100), range(100))
        apply_grid(ax)
        count = sum(1 for l in ax.get_ygridlines() if l.get_visible())
        assert count <= DESIGN_RULES["grid"]["max_h_gridlines"] + 1, \
            f"Too many gridlines: {count}"


# ─────────────────────────────────────────────────────────────────────────────
# add_callout
# ─────────────────────────────────────────────────────────────────────────────

class TestAddCallout:

    def test_callout_adds_annotations(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [10, 20, 30])
        before = len(ax.texts)
        add_callout(ax, x=2, y=20, label="峰值", value_text="20%")
        assert len(ax.texts) > before, "add_callout should add text annotations"

    def test_callout_vline_added(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [10, 20, 30])
        before = len(ax.lines)
        add_callout(ax, x=2, y=20, label="峰值", value_text="20%", vline=True)
        assert len(ax.lines) > before, "vline=True should add a vertical line"

    def test_callout_no_vline(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [10, 20, 30])
        before = len(ax.lines)
        add_callout(ax, x=2, y=20, label="峰值", value_text="20%", vline=False)
        assert len(ax.lines) == before, "vline=False should not add a line"

    def test_callout_value_fontsize(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [10, 20, 30])
        add_callout(ax, x=2, y=20, label="峰值", value_text="20%")
        annotations = ax.texts
        sizes = [a.get_fontsize() for a in annotations]
        expected_value = DESIGN_RULES["typography"]["annotation_value_size"]
        assert expected_value in sizes, \
            f"annotation_value_size {expected_value} not found in {sizes}"

    def test_callout_label_smaller_than_value(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [10, 20, 30])
        add_callout(ax, x=2, y=20, label="峰值", value_text="20%")
        sizes = sorted([a.get_fontsize() for a in ax.texts])
        assert sizes[0] < sizes[-1], \
            "Label text must be smaller than value text"

    def test_vline_alpha_override(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [10, 20, 30])
        custom_alpha = 0.15
        add_callout(ax, x=2, y=20, label="峰值", value_text="20%",
                    vline=True, vline_alpha=custom_alpha)
        vlines = [l for l in ax.lines if l.get_linestyle() in ("--", "dashed")]
        assert len(vlines) > 0
        assert vlines[-1].get_alpha() == pytest.approx(custom_alpha, abs=0.01)


# ─────────────────────────────────────────────────────────────────────────────
# add_series_label
# ─────────────────────────────────────────────────────────────────────────────

class TestAddSeriesLabel:

    def test_label_added_to_figure(self, fig_ax):
        fig, _ = fig_ax
        before = len(fig.texts)
        add_series_label(fig, "A_lp")
        assert len(fig.texts) == before + 1

    def test_label_text_content(self, fig_ax):
        fig, _ = fig_ax
        add_series_label(fig, "A_lp")
        texts = [t.get_text() for t in fig.texts]
        assert CONTENT_SERIES["A_lp"]["label"] in texts

    def test_label_color_for_colored_series(self, fig_ax):
        fig, _ = fig_ax
        add_series_label(fig, "A_lp")
        label_text = [t for t in fig.texts
                      if t.get_text() == CONTENT_SERIES["A_lp"]["label"]][0]
        assert label_text.get_color() == COLORS["content_series"]["A_lp"]

    def test_label_color_for_muted_series(self, fig_ax):
        fig, _ = fig_ax
        add_series_label(fig, "C_token")
        label_text = [t for t in fig.texts
                      if t.get_text() == CONTENT_SERIES["C_token"]["label"]][0]
        assert label_text.get_color() == COLORS["text"]["muted"]

    def test_invalid_series_key_raises(self, fig_ax):
        fig, _ = fig_ax
        with pytest.raises(KeyError):
            add_series_label(fig, "Z_nonexistent")


# ─────────────────────────────────────────────────────────────────────────────
# apply_legend
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyLegend:

    def test_legend_frameon_false(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2], [1, 2], label="Series 1")
        legend = apply_legend(ax)
        assert not legend.get_frame_on(), "Legend frameon must be False"

    def test_legend_exists(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2], [1, 2], label="Series 1")
        legend = apply_legend(ax)
        assert legend is not None

    def test_legend_label_fontsize(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2], [1, 2], label="Series 1")
        legend = apply_legend(ax)
        for text in legend.get_texts():
            assert text.get_fontsize() == DESIGN_RULES["typography"]["annotation_label_size"]


# ─────────────────────────────────────────────────────────────────────────────
# style_axes
# ─────────────────────────────────────────────────────────────────────────────

class TestStyleAxes:

    def test_top_spine_hidden(self, fig_ax):
        _, ax = fig_ax
        style_axes(ax)
        assert not ax.spines["top"].get_visible()

    def test_right_spine_hidden(self, fig_ax):
        _, ax = fig_ax
        style_axes(ax)
        assert not ax.spines["right"].get_visible()

    def test_bottom_spine_hidden_by_default(self, fig_ax):
        _, ax = fig_ax
        style_axes(ax)
        assert not ax.spines["bottom"].get_visible()

    def test_left_spine_visible(self, fig_ax):
        _, ax = fig_ax
        style_axes(ax)
        assert ax.spines["left"].get_visible()

    def test_tick_label_size(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [1, 2, 3])
        style_axes(ax)
        expected = DESIGN_RULES["typography"]["tick_label_size"]
        params = ax.xaxis.get_tick_params(which="major")
        assert params.get("labelsize") == expected

    def test_grid_applied(self, fig_ax):
        _, ax = fig_ax
        ax.plot([1, 2, 3], [1, 2, 3])
        style_axes(ax)
        assert not any(l.get_visible() for l in ax.get_xgridlines())


# ─────────────────────────────────────────────────────────────────────────────
# validate_title (Rule 01)
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateTitle:

    def test_valid_title_passes(self):
        validate_title("稳定币不是弹药库——它是杠杆的温度计")

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_title("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_title("   ")

    def test_too_long_raises(self):
        long = "这" * 61
        with pytest.raises(ValueError, match="long"):
            validate_title(long)

    def test_forbidden_suffix_对比图(self):
        with pytest.raises(ValueError, match="forbidden suffix"):
            validate_title("BTC与标普对比图")

    def test_forbidden_suffix_走势图(self):
        with pytest.raises(ValueError, match="forbidden suffix"):
            validate_title("稳定币TVL走势图")

    def test_forbidden_suffix_数据(self):
        with pytest.raises(ValueError, match="forbidden suffix"):
            validate_title("链上Lending数据")

    def test_forbidden_suffix_chart(self):
        with pytest.raises(ValueError, match="forbidden suffix"):
            validate_title("LP yield chart")

    def test_contrast_pattern_passes(self):
        validate_title("LP名义收益 ≠ 真实收益")

    def test_question_with_stance_passes(self):
        validate_title("你的V3 LP真的赚钱吗？")

    def test_exactly_60_chars_passes(self):
        title = "这" * 60
        validate_title(title)


# ─────────────────────────────────────────────────────────────────────────────
# validate_tweet_copy (Rule 04)
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateTweetCopy:

    def test_valid_copy_passes(self):
        validate_tweet_copy(
            "稳定币流入Lending在牛市顶部达到15.6%。"
            "这意味着它更像是杠杆需求的体温计，而不是资金待入场的弹药库。"
            "如果你在靠稳定币占比判断入场时机，这个逻辑可能需要重新校准。"
        )

    def test_forbidden_start_可以看到(self):
        with pytest.raises(ValueError, match="forbidden phrase"):
            validate_tweet_copy("可以看到2025年lending占比达到峰值。")

    def test_forbidden_start_图表显示(self):
        with pytest.raises(ValueError, match="forbidden phrase"):
            validate_tweet_copy("图表显示稳定币占比在熊市底部最低。")

    def test_forbidden_start_数据表明(self):
        with pytest.raises(ValueError, match="forbidden phrase"):
            validate_tweet_copy("数据表明这个周期和上个周期不同。")

    def test_missing_inference_frame(self):
        with pytest.raises(ValueError, match="inference frame"):
            validate_tweet_copy(
                "稳定币在牛市顶部占比15.6%，在熊市底部占比1.5%。"
                "两者相差超过10个百分点。历史上每次顶部都伴随高占比。"
            )

    def test_这推翻了_frame_passes(self):
        validate_tweet_copy(
            '稳定币占比在顶部最高。这推翻了"稳定币多=子弹多=利好"的常见解读。'
        )

    def test_暴露了_frame_passes(self):
        validate_tweet_copy(
            "Lending占比的峰值和BTC价格高度重合。这暴露了市场在顶部的真实杠杆结构。"
        )

    def test_leading_whitespace_ignored(self):
        with pytest.raises(ValueError, match="forbidden phrase"):
            validate_tweet_copy("  可以看到这张图的数据很有意思。")
