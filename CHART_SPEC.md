# Crypto Charts Design Spec

This project generates dark, professional crypto data charts for publishing on X (@koalada18).
Every chart must use the shared theme (`config/theme.py`) and reusable components so visuals stay consistent across posts.

> **Project context**: see `docs/STRATEGY.md` for account positioning, master theme,
> and content series taxonomy. Every new chart MUST belong to a defined content series
> or an approved exception slot.

## Visual Rules

- Canvas: `1200 x 675 px`, `150 DPI`, 16:9 ratio.
- Background: `#0A0E1A` (midnight base).
- Surface: `#0D1426` for future panels or framed components.
- Grid: `#111D35`.
- Primary data color: `#4FC3F7` (ice blue).
- Accent data color: `#FFD166` (warm gold).
- Tertiary / quaternary data: `#A8FF78` lime, `#A78BFA` violet.
- Up / down: `#4FC3F7` / `#EF5350`.
- Difference / eroded portion: `#475569` (Series A specifically).
- Text: `#E8F0FF` primary, `#6B84B8` muted, `#2E3F6B` hint, `#6B7280` footer.
- Typography: read sizes and weights from `config/theme.py` `TYPOGRAPHY`.
- Footer font: monospace (Menlo / JetBrains Mono / IBM Plex Mono).
- Never hardcode visual constants in chart or component modules.
- Color references in code MUST use the nested structure in `COLORS`
  (e.g. `COLORS["data"]["primary"]`, NOT `COLORS["primary"]`).

## Layout Rules

- Title and subtitle sit in the upper-left area.
- Content series identifier (label) sits below subtitle, left-aligned.
- Main price chart uses `LAYOUT["price_axes"]`.
- Volume uses `LAYOUT["volume_axes"]`.
- Source attribution sits in the lower-left corner.
- Watermark `@koalada18` uses `LAYOUT["watermark_x/y"]` (lower-right).
  - **Note**: footer slot at `LAYOUT["footer_x/y"]` (centered bottom) is reserved
    for future use; current charts continue using corner watermark.
- Large callouts use `LAYOUT["callout_default"]` unless an exception is added to `theme.py`.
- **No insight box**: deprecated and permanently removed. Personal analysis belongs
  in the tweet body, NOT inside the chart.

## Component Rules

- Use `BaseChart` for figure creation, titles, source text, watermark, footer, and saving.
- Use `PriceLine` for price series rendering and high/low annotations.
- Use `VolumeBar` for volume rendering and up/down coloring.
- Use `Annotations` for callouts, event lines, and percentage changes.
- Data fetching must stay in `data/`; rendering code must stay in `components/` and `charts/`.
- Each file in `charts/` produces exactly one chart type.

## Series Layer Spec

Every chart belongs to exactly one of:
- A defined content series (A through F), OR
- An approved exception slot (`X_macro` for macro reference content)

### Series Registry

Defined in `theme.CONTENT_SERIES`. Current entries:

| Code | Label | Color | Visible Color |
|------|-------|-------|---------------|
| `A_lp` | LP 收益幻觉 | `#C4A8FF` | yes |
| `B_yield` | 收益率拆解 | `#F4A261` | yes |
| `C_token` | 代币激励的真实账 | `text.muted` | no |
| `D_narrative` | DeFi 叙事周期 | `text.muted` | no |
| `E_risk` | DeFi 风险结构 | `#E76F51` | yes |
| `F_ranking` | 榜单幻觉 | `text.muted` | no |
| `X_macro` | 宏观参照 | `text.muted` | no |

### Content-Series Color Usage

`content_series` colors are HIGHLY restricted:
1. **Series identifier label** below subtitle (always)
2. **Optional 2px title side-bar** for visual emphasis (Series A/B/E only)
3. **At most ONE key number per chart** as colored emphasis (the "punch number")

**FORBIDDEN**: using `content_series` colors for data lines, bars, areas, or any
quantitative encoding. Data visualization MUST use `data.*` palette only.

### Subtitle Format (Required from Series A onward)
Source: <source1>, <source2> | Period: <start> to <end> | Method: <core method>

- All three segments are mandatory.
- `Method` is non-negotiable — it must describe how the headline number was computed
  (e.g. `Net Return = Fees + Rewards (sold) − IL − Gas`).

### Title Side-Bar (Optional)

For Series A / B / E, an optional 2px vertical color bar may sit immediately to the
left of the title, height ≈ `STYLE["title_sidebar_height_ratio"]` × title font size.
Color = corresponding `content_series` color.

## Series A · LP Yield Illusion — Content Spec

### Definition

Charts that compute the *true* return of LP positions after stripping out token reward
volatility, sell pressure, opportunity cost, and hedging costs.

### Scope (✅ in / ❌ out)

- ✅ True PnL accounting of LP positions
- ✅ Decomposition of LP return components (fees / rewards / IL / rebalance / opp-cost)
- ✅ Comparing LP strategies, protocols, or LP vs. alternative holdings
- ❌ How-to / operation tutorials (those are guides, not research)
- ❌ "Which pool has highest APR right now" (that's market commentary)
- ❌ Predicting future LP returns

### Title Patterns (pick one)

- **Contrast**: `X ≠ Y` or `X looks A, but actually B`
  - Example: `AMM 综合排名第一 ≠ LP 真实收益第一`
- **Question with stance**: question that already implies the contrarian answer
  - Example: `你的 V3 LP 真的赚钱吗?`
- **Accounting**: surface the hidden cost explicitly
  - Example: `LP 收益减去机会成本之后,还剩多少`

**Forbidden patterns**: descriptive titles (`AMM 综合评分对比`), neutral questions
without stance (`LP 收益怎么算?`), clickbait (`90% 的 LP 都在亏!`).

### Tweet Body Structure (3 paragraphs)

1. **Thesis (1-2 sentences)**: state the conclusion directly, echoing the chart title in conversational tone.
2. **Why (2-3 sentences)**: unpack the core logic. **Include first-person empirical evidence** ("我自己的 LP 头寸数据" / "我亲自对比过两个池子").
3. **What it means for the reader (1-2 sentences)**: not "you should X", but "if you're doing X, you may have overlooked Y". Expose blind spot, leave decision to reader.

**Forbidden in tweets**:
- Long thread (main tweet must be single, thread max 3 with first standalone)
- Social filler ("感兴趣的可以..." / "欢迎讨论")
- Promotional links / product pitches

### Data Color Mapping (Series A)

- Nominal yield / APR → `data.primary` (ice blue)
- True yield / adjusted return → `data.accent` (warm gold)
- Difference / eroded portion → `data.diff` (`#475569`, dark neutral)

This three-color split visually carries the thesis: nominal eroded by reality.
Color does argument work, not decoration.

### Series A Aux Color

`#C4A8FF` is reserved for:
- Series A label text under subtitle
- Optional title side-bar
- At most ONE key number emphasis (the "punch" — usually the true-return number)

## New Chart Workflow

1. **Confirm series membership**: which content series does this chart belong to? If none, it must qualify as `X_macro` exception (max 2/quarter total). If neither, do NOT build it.
2. Add or reuse a fetcher in `data/fetcher.py`.
3. Create one chart module under `charts/`.
4. Fetch data first and transform it into a clean DataFrame.
5. Initialize `BaseChart`.
6. Add themed axes using layout constants from `config/theme.py`.
7. Draw reusable components from `components/`, applying series-specific color mapping if defined.
8. Render series identifier label below subtitle.
9. Add source attribution (with `Method:` segment), watermark, and footer.
10. Save into `output/`.
11. Add a focused test when new theme fields or reusable behavior are introduced.

## Prompt Templates

### General Chart Prompt

```text
Create a new crypto chart in this project for [asset/protocol/metric].
Use the existing theme from config/theme.py and only draw through reusable components.
Fetch data in data/fetcher.py if a new endpoint is required.
Create one new chart file in charts/ named [chart_name].py.
The chart should include title, subtitle (with Method:), source, watermark, and save to output/[chart_name].png.
Do not hardcode colors, fonts, canvas size, or layout dimensions outside config/theme.py.
Run the chart script and relevant tests after implementation.
```

### Series A Chart Prompt (LP Yield Illusion)

```text
Create a new Series A (LP 收益幻觉) chart for [specific LP topic].
This chart must follow CHART_SPEC.md "Series A" content rules:
- Title pattern: contrast / question-with-stance / accounting (pick one).
- Subtitle MUST include Source, Period, Method.
- Render content series identifier "LP 收益幻觉" below subtitle in COLORS["content_series"]["A_lp"].
- Data color mapping: nominal=data.primary, true/adjusted=data.accent, diff=data.diff.
- Aux color #C4A8FF: series label + optional title side-bar + at most 1 key number emphasis.
- NO insight box. Personal analysis goes in the tweet body.

Use config/theme.py only. Reusable components only.
Save to output/[chart_name].png.
After implementation, output the proposed tweet body in 3-paragraph structure
(thesis / why-with-first-person-evidence / what-it-means-for-reader).
```

## Reference Documents

- `docs/STRATEGY.md` — account positioning, master theme, content series taxonomy
- `docs/观点库.md` — selection pool with metadata
- `CHART_SPEC.md` — this file (visual + content production rules)

## Design Rules  （从 config/theme.py DESIGN_RULES 提炼的执行标准）

所有图表生成代码必须通过 `tests/test_design_rules.py`。违反以下任何规则，
Codex 生成的代码不得提交。

---

### Rule 01 — Title = Thesis

```
标题是论点，不是描述。
```

| 项目 | 要求 |
|------|------|
| 字号 | `DESIGN_RULES["typography"]["title_size"]`（默认18pt），最小不低于 `DESIGN_RULES["title"]["min_font_size"]`（16pt） |
| 长度 | ≤ 60 字符 |
| 格式 | 必须是可被反驳的主张句。禁止以「对比图」「走势图」「数据」「图表」「overview」「chart」结尾 |

**Codex 指令片段**：
> 标题变量命名为 `CHART_TITLE`，内容必须是一个中文主张句（可被反驳的结论），
> 不得以描述性词语结尾。字号引用 `DESIGN_RULES["typography"]["title_size"]`。

---

### Rule 02 — Color = Signal Only

```
颜色只分配给有语义的概念，不分配给序号。
灰色处理其余一切。
```

| 元素 | 颜色规则 |
|------|---------|
| 主数据线 | `COLORS["series"]["a"]` 或指定颜色 |
| 次要/对比数据线 | `COLORS["series"]["b"]` |
| 参考线 / 标注竖线 | `color="white"` + `alpha=DESIGN_RULES["color"]["annotation_line_alpha"]`（0.30） |
| 面积填充（主） | 主线色 + `alpha=DESIGN_RULES["color"]["fill_alpha_primary"]`（0.25） |
| 面积填充（次） | 次线色 + `alpha=DESIGN_RULES["color"]["fill_alpha_secondary"]`（0.12） |
| 格线 | `COLORS["base"]["grid"]` + `alpha=DESIGN_RULES["color"]["gridline_alpha"]`（0.18） |
| 轴刻度标签 | `COLORS["text"]["muted"]` + `alpha=DESIGN_RULES["color"]["axis_label_alpha"]`（0.55） |
| 单图最多有色 hue 数 | **3**，超过则重构配色 |

**双轴图额外规则**：左轴刻度颜色 = 左侧数据线颜色；右轴刻度颜色 = 右侧数据线颜色。
调用 `chart_utils._apply_dual_axis_colors(ax_left, ax_right, color_left, color_right)`。

---

### Rule 03 — Grid = Navigation, Not Decoration

```
格线帮读者对齐数值。多余的格线是噪音。
```

| 项目 | 要求 |
|------|------|
| 水平格线数量 | `ax.yaxis.set_major_locator(plt.MaxNLocator(DESIGN_RULES["grid"]["max_h_gridlines"]))` |
| 垂直格线 | 默认关闭；仅在时间序列密度极高时可选开启，需注释说明原因 |
| 格线样式 | `linestyle=DESIGN_RULES["grid"]["gridline_style"]`（`"--"`），`linewidth=DESIGN_RULES["grid"]["gridline_linewidth"]`（0.5） |
| 格线颜色 | `COLORS["base"]["grid"]` |

**Codex 指令片段**：
> 调用 `ax.grid()` 时必须写 `axis="y"`，样式从 `DESIGN_RULES["grid"]` 取值。
> 禁止写 `ax.grid(True)` 或不带参数的 `ax.grid()`。

---

### Rule 04 — Insight = Inference  （tweet copy 层，不在图上）

```
Insight box 已从图表画布永久移除。
观点写在推文正文。正文必须包含推断框架，不得复述图表。
```

推文正文生成时（Codex 或手写）必须通过以下检查：

- **禁止开头**：「可以看到」「图表显示」「数据表明」「从图中」「如图所示」
- **必须包含**（至少其一）：「这意味着」「这说明」「这推翻了」「这暴露了」「这改变了」

测试函数：`tests/test_design_rules.py::TestInsightFraming`

---

### Rule 05 — Whitespace = Precision

```
数据区域占画布约 65%。边距慷慨，不拥挤。
```

使用 `fig.subplots_adjust()` 应用以下值（从 `DESIGN_RULES["layout"]` 取）：

```python
fig.subplots_adjust(
    left   = DESIGN_RULES["layout"]["margin_left"],    # 0.10
    right  = 1 - DESIGN_RULES["layout"]["margin_right"],  # 0.90
    top    = 1 - DESIGN_RULES["layout"]["margin_top"],    # 0.86
    bottom = DESIGN_RULES["layout"]["margin_bottom"],  # 0.12
)
```

图例位置：`ax.legend(bbox_to_anchor=(0.01, 0.99), loc="upper left", borderaxespad=0)`
图例不得遮挡数据区域，`frameon=False`。

---

### Rule 06 — Typography Hierarchy

```
层级差必须视觉可感。字号比例 >= 1.5x（标题:副标题）。
```

引用 `DESIGN_RULES["typography"]`，所有字号必须从该字典取值，不得硬编码：

```python
T = DESIGN_RULES["typography"]

ax.set_title(CHART_TITLE, fontsize=T["title_size"],   color=COLORS["text"]["primary"],   pad=14)
ax.text(...)              # subtitle:  fontsize=T["subtitle_size"]
ax.set_xlabel(...)        # axis label: fontsize=T["axis_label_size"]
ax.tick_params(labelsize=T["tick_label_size"])

# Annotation callouts: value larger than label
# value text:  fontsize=T["annotation_value_size"]
# label text:  fontsize=T["annotation_label_size"]
```

**测试保证**：`typography_valid()` 函数在 `config/theme.py` 中，
`tests/test_design_rules.py::TestTypographyHierarchy::test_valid_hierarchy_passes` 会在
每次 `DESIGN_RULES` 修改后自动验证比例一致性。
