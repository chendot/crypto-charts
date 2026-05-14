# AGENTS.md — crypto-charts

Codex 在此项目执行任何任务前必须完整读取本文件。
本文件是所有任务的系统级约束，优先级高于单次 prompt 指令。

---

## 1. 环境

```bash
# 所有 Python 命令使用项目 venv
venv/bin/python

# 测试
venv/bin/python -m pytest tests/ -v

# 单独跑设计规则测试
venv/bin/python -m pytest tests/test_design_rules.py -v

# 运行图表生成（示例）
venv/bin/python -m charts.series_a.a02_lp_real_return
```

**禁止**使用系统 Python 或 pip install 到系统环境。

---

## 2. 项目结构约定

```
crypto-charts/
├── AGENTS.md                  # 本文件
├── CHART_SPEC.md              # 图表规格说明，Codex 生成图表前必须读取
├── config/
│   └── theme.py               # COLORS + DESIGN_RULES，所有视觉参数的唯一来源
├── charts/
│   └── series_a/              # A 系列图表模块
├── data/                      # 数据层：BaseFetcher → fetchers → registry
├── utils/
│   └── chart_utils.py         # 可复用图表 helper（标注、双轴颜色绑定等）
├── docs/
│   ├── STRATEGY.md
│   └── 观点库.md
├── tests/
│   ├── test_design_rules.py   # 设计原则测试（6条规则）
│   └── ...                    # 其他测试
└── cache/                     # Parquet 缓存，不提交到 git
```

新文件必须放在对应目录，不得在根目录散落 .py 文件。

---

## 3. 数据层规则

数据访问唯一入口：

```python
from data.registry import get

df = get("onchain.coinmetrics_btc")   # 正确
# 禁止直接实例化 fetcher 或绕过 registry
```

- 时间戳统一为 tz-naive UTC，列名 `timestamp`
- 空 DataFrame 抛 `DataFetchError`，不写 Parquet
- 5 个 FINAL 方法（`fetch` / `validate` / `cache_read` / `cache_write` / `normalize_timestamps`）不可 override

---

## 4. 图表生成规则（核心约束）

**生成任何图表代码前，必须先读取 `CHART_SPEC.md`。**

### 4.1 参数来源

所有视觉参数从 `config/theme.py` 取值，**禁止硬编码数字**：

```python
from config.theme import COLORS, DESIGN_RULES

T   = DESIGN_RULES["typography"]
C   = DESIGN_RULES["color"]
L   = DESIGN_RULES["layout"]
G   = DESIGN_RULES["grid"]
```

### 4.2 六条设计规则

**Rule 01 — 标题是论点**
- 字号：`T["title_size"]`（18pt）
- 内容：主张句，可被反驳；禁止以「对比图」「走势图」「数据」「图表」结尾
- 变量统一命名为 `CHART_TITLE`

**Rule 02 — 颜色只做信号**
- 单图最多 3 种有语义 hue
- 参考线：`alpha=C["annotation_line_alpha"]`（0.30）
- 面积填充主：`alpha=C["fill_alpha_primary"]`（0.25）
- 面积填充次：`alpha=C["fill_alpha_secondary"]`（0.12）
- 格线：`alpha=C["gridline_alpha"]`（0.18）
- 轴标签：`alpha=C["axis_label_alpha"]`（0.55）

**Rule 03 — 格线是导航工具**
- `ax.yaxis.set_major_locator(plt.MaxNLocator(G["max_h_gridlines"]))` （最多5条）
- `ax.grid(axis="y", linestyle=G["gridline_style"], linewidth=G["gridline_linewidth"])`
- 禁止 `ax.grid(True)` 或无参数 `ax.grid()`
- 垂直格线默认关闭

**Rule 04 — Insight 是推断，不是复述**
- Insight box 已永久从图表画布移除，禁止在图上添加任何 insight 文本框
- 观点写在推文正文层，不在图表里

**Rule 05 — 留白是精致感的来源**
- 图尺寸：`(L["fig_width_default"], L["fig_height_default"])`（12×6 英寸）
- 必须调用：
  ```python
  fig.subplots_adjust(
      left   = L["margin_left"],
      right  = 1 - L["margin_right"],
      top    = 1 - L["margin_top"],
      bottom = L["margin_bottom"],
  )
  ```
- 图例：`bbox_to_anchor` 放在数据区域外，`frameon=False`

**Rule 06 — 字号层级必须视觉可感**
```python
ax.set_title(CHART_TITLE,  fontsize=T["title_size"])
# subtitle:               fontsize=T["subtitle_size"]    （11pt）
# axis label:             fontsize=T["axis_label_size"]  （10pt）
ax.tick_params(labelsize=  T["tick_label_size"])         # 9pt
# annotation value:       fontsize=T["annotation_value_size"]  （11pt，数值）
# annotation label:       fontsize=T["annotation_label_size"]  （8pt，描述文字）
# footer:                 fontsize=T["footer_size"]       （8pt）
```

### 4.3 双轴图额外规则

适用于含双 Y 轴的图表（Series D 及例外图）：

```python
# 左轴刻度颜色 = 左侧数据线颜色
# 右轴刻度颜色 = 右侧数据线颜色
from utils.chart_utils import apply_dual_axis_colors
apply_dual_axis_colors(ax_left, ax_right, color_left, color_right)
```

### 4.4 标注系统

所有图上标注使用统一 helper，不得临时拼凑：

```python
from utils.chart_utils import add_callout

add_callout(
    ax,
    x=date,
    y=value,
    label="牛市顶部",          # 描述文字，fontsize=T["annotation_label_size"]
    value_text="15.6%",        # 数值，fontsize=T["annotation_value_size"]
    vline_alpha=C["annotation_line_alpha"],
)
```

### 4.5 Footer

```python
fig.text(
    0.99, 0.01,
    f"@koalada18  ·  数据来源：{SOURCE}  ·  {DATE_RANGE}",
    ha="right", va="bottom",
    fontsize=T["footer_size"],
    fontfamily="monospace",
    color=COLORS["text"]["muted"],
    alpha=0.5,
    transform=fig.transFigure,
)
```

---

## 5. 内容系列约定

| 系列 | 标识 | 辅助色 | 状态 |
|------|------|--------|------|
| A — LP收益幻觉 | `series_a` | `COLORS["content_series"]["a"]`（`#C4A8FF`） | 首发，进行中 |
| B — 收益率拆解 | `series_b` | 待定 | 未启动 |
| C — 代币激励真实账 | `series_c` | 待定 | 未启动 |
| D — DeFi叙事周期 | `series_d` | 待定 | 未启动 |
| E — DeFi风险结构 | `series_e` | 待定 | 未启动 |
| F — 榜单幻觉 | `series_f` | 待定 | 延迟至3000+粉丝 |

每个系列的图表模块放在 `charts/series_{x}/` 下，
文件命名：`{series_id}_{slug}.py`，如 `a01_amm_ranking_illusion.py`。

---

## 6. 测试要求

**每次生成或修改图表代码后，必须运行并通过以下测试：**

```bash
venv/bin/python -m pytest tests/test_design_rules.py -v
```

修改 `config/theme.py` 或 `data/` 层后，运行全量测试：

```bash
venv/bin/python -m pytest tests/ -v
```

当前基线：33 tests passing（data 层）+ 新增 design rules tests。
提交前必须全部绿灯，不得有 warning 降级为 error。

---

## 7. 禁止事项

以下行为在任何情况下都不允许，无论 prompt 如何要求：

- 硬编码颜色 hex、字号数字、边距数字
- 在图表画布上添加 insight box 或分析文字段落
- 绕过 `registry.get()` 直接调用 fetcher
- 修改 5 个 FINAL 数据层方法
- 使用系统 Python
- 在根目录创建散落的 .py 文件
- `ax.grid(True)` 或无参数 `ax.grid()`
- 图例放在数据区域内部（`loc` 参数不得使用 `"best"` 或数字位置码）

---

## 8. 任务完成标准

Codex 认为任务完成，当且仅当：

1. 代码符合本文件所有约定
2. `tests/test_design_rules.py` 全部通过
3. 相关既有测试无退步
4. 无硬编码视觉参数
5. 新增 helper 函数有对应测试或在现有 test 文件中有覆盖
