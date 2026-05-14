# Crypto Charts

面向 X 账号 `@koalada18` 的加密市场数据图表生产框架。

这个项目的目标不是临时画几张图，而是把一套长期可复用的图表生产流程固定下来：数据获取、缓存、校验、主题系统、可复用绘图组件、模板注册、内容系列规则和测试约束都集中管理。这样每次生成新图表时，视觉风格、数据口径和发布表达不会漂移。

## 工程目标

`crypto-charts` 主要解决三件事：

1. 生成适合 X 发布的深色专业图表，默认输出 `1200 x 675 px`、`150 DPI` 的 PNG。
2. 把图表设计原则变成可执行约束，避免标题、颜色、格线、字号、留白和 insight 表达在不同图表之间失控。
3. 支持长期内容系列和周期性模板，让常用主题可以复用数据层和组件层，按日期稳定再生成。

当前核心方向是加密市场研究图表，重点覆盖：

- BTC ETF 资金流结构
- BTC 周期与宏观参照
- DeFi / LP 收益幻觉
- 收益率拆解
- 代币激励真实账
- DeFi 叙事周期
- DeFi 风险结构
- 稳定币、跨链流动和链上资金迁移

## 当前状态

项目已经具备完整的基础框架：

- 统一主题系统：`config/theme.py`
- 六条设计原则测试：`tests/test_design_rules.py`
- 图表 helper 测试：`tests/test_chart_utils.py`
- 数据层 registry / fetcher / schema / cache 基础设施
- 模板注册系统：`config/templates.py`
- 可复用 Matplotlib 组件：`components/`
- 周期性模板目录：`templates/`
- 手工或旧版单图入口：`charts/`

当前全量测试基线：

```text
114 passed, 2 warnings
```

其中 warnings 来自测试数据的 stale-data 提示，不影响通过。

## 目录结构

```text
crypto-charts/
├── AGENTS.md                  # Codex 项目级执行约束
├── CHART_SPEC.md              # 图表视觉、内容系列和生成规则
├── PROJECT_SPEC.md            # 工程架构、数据契约、模板契约
├── TEMPLATE_SPEC.md           # 周期性模板规划说明
├── README.md                  # 本文件
├── conftest.py                # 让 pytest 将项目根目录加入 import path
├── config/
│   ├── theme.py               # COLORS / TYPOGRAPHY / LAYOUT / DESIGN_RULES
│   └── templates.py           # T1-T7 模板注册与文案元数据
├── components/                # 可复用绘图组件
├── charts/                    # 单图脚本或旧版图表入口
├── templates/                 # 周期性图表模板 T1-T7
├── data/                      # 数据层：fetchers / registry / schemas / cache
├── utils/
│   └── chart_utils.py         # 设计规则 helper：格线、双轴、标注、图例等
├── scripts/                   # 命令行工具，例如 render_one.py
├── docs/                      # 策略、选题、数据源说明
├── tests/                     # pytest 测试
├── output/                    # 生成的 PNG，通常不提交
└── outputs/                   # 部分实验输出
```

## 架构分层

项目按单向依赖组织：

```text
templates/  ->  components/  ->  config/
     │
     └──────>  data/         ->  data helpers
```

约束如下：

- `templates/` 负责图表编排：取数据、调用组件、套用模板文案并保存 PNG。
- `components/` 只负责可复用视觉元素，不读取远端数据。
- `data/` 负责抓取、缓存、归一化和校验 DataFrame，不依赖绘图组件。
- `config/theme.py` 是所有视觉参数的唯一来源。
- `utils/chart_utils.py` 放置设计规则相关 helper，例如 `apply_grid()`、`add_callout()`、`apply_dual_axis_colors()`。

## 数据层约定

数据访问统一通过 registry：

```python
from data.registry import get

df = get("onchain.coinmetrics_btc")
```

不要在图表或模板里直接实例化 fetcher，也不要直接解析远端 API 原始响应。

数据层的基本要求：

- 时间戳统一为 tz-naive UTC。
- 标准时间列根据数据集使用 `date` 或 `timestamp`。
- fetcher 返回归一化后的 `pandas.DataFrame`。
- 空 DataFrame 应抛出 `DataFetchError`，不写入缓存。
- schema 声明集中在 `data/schemas.py`。
- 缓存优先使用 `data/cache/` 下的 parquet。

## 图表设计原则

六条设计原则已经从文档落成测试约束：

1. 标题是论点，不是描述。
2. 颜色只做信号，不做装饰。
3. 格线是导航工具，不制造噪音。
4. Insight 是推断，写在正文层，不放进图表画布。
5. 留白是精致感的来源。
6. 字号层级必须视觉可感。

生成或修改图表代码前必须阅读 `CHART_SPEC.md`。所有颜色、字号、边距、alpha、格线参数都从 `config/theme.py` 读取，禁止在图表代码里硬编码视觉常量。

常用 helper：

```python
from utils.chart_utils import (
    add_callout,
    add_series_label,
    apply_dual_axis_colors,
    apply_grid,
    apply_legend,
    style_axes,
)
```

## 模板系统

周期性模板由 `config/templates.py` 注册，模板实现放在 `templates/`。

| ID | 名称 | 状态 |
| --- | --- | --- |
| T1 | BTC Spot ETF Flow Structure | 已实现 |
| T2 | BTC Halving Cycle Normalized Comparison | 脚手架 |
| T3 | Historical Top-Buyer Drawdown Comparison | 脚手架 |
| T4 | LP and Staking Real Yield Ranking | 脚手架 |
| T5 | Funding-Rate Extremes Forward Return Distribution | 脚手架 |
| T6 | Narrative Sector Rotation Bump Chart | 已实现 |
| T7 | Cross-Chain Stablecoin Flow Sankey | 脚手架 |

每个模板模块应暴露：

```python
def render(as_of: date | str | None = None, variant: str | None = None) -> Path:
    """Render a chart through the requested cutoff date and return the PNG path."""
```

未实现模板会主动抛出 `NotImplementedError`，这是预期行为。

## 环境准备

项目要求使用本地 venv，禁止使用系统 Python。

安装依赖：

```bash
venv/bin/pip install -r requirements.txt
```

所有 Python 命令都应使用：

```bash
venv/bin/python
```

## 使用说明

渲染注册模板：

```bash
venv/bin/python scripts/render_one.py t1 --as-of 2026-05-04
```

部分模板支持手动标题覆盖：

```bash
venv/bin/python scripts/render_one.py t1 --as-of 2026-05-04 --title "Custom title"
```

运行单图脚本：

```bash
venv/bin/python charts/btc_30d.py
venv/bin/python charts/macro_comparison_5y.py
venv/bin/python charts/btc_nasdaq_correlation.py
```

新增系列图表后，也可以按模块形式运行：

```bash
venv/bin/python -m charts.series_a.<chart_module>
```

生成图片默认写入 `output/` 或脚本指定的输出目录。

## 测试

全量测试：

```bash
venv/bin/python -m pytest tests/ -v
```

设计原则测试：

```bash
venv/bin/python -m pytest tests/test_design_rules.py -v
```

图表 helper 测试：

```bash
venv/bin/python -m pytest tests/test_chart_utils.py -v
```

数据层或主题层有改动时，必须跑全量测试。只改图表代码时，至少跑设计原则测试和相关图表测试。

## 新增图表工作流

新增图表建议按这个顺序走：

1. 阅读 `AGENTS.md` 和 `CHART_SPEC.md`。
2. 确认图表属于哪一个内容系列，或是否是允许的 `X_macro` 例外。
3. 确认数据源和指标口径，优先复用 `data/` 现有 fetcher。
4. 通过 `data.registry.get()` 获取数据，不绕过 registry。
5. 复用 `components/` 和 `utils/chart_utils.py`，不要临时拼装重复视觉逻辑。
6. 所有视觉参数从 `config/theme.py` 获取。
7. 图表标题使用 `CHART_TITLE`，标题必须是可被反驳的中文主张句。
8. 图上不添加 insight box；观点写在推文正文层。
9. 保存 PNG 到 `output/`。
10. 运行相关测试，确认无退步。

标准收尾命令：

```bash
venv/bin/python -m pytest tests/test_design_rules.py -v
venv/bin/python -m pytest tests/ -v
```

## 开发规范

- 不在根目录散落新的 `.py` 文件。
- 不硬编码颜色 hex、字号数字、边距数字或 alpha。
- 不使用 `ax.grid(True)` 或无参数 `ax.grid()`。
- 双轴图必须调用 `apply_dual_axis_colors()`。
- 图上标注使用 `add_callout()`。
- 图例放在数据区域外，`frameon=False`。
- 新增 helper 函数需要有对应测试，或在现有测试中覆盖。
- 提交前确认测试全绿。

## 参考文档

- `AGENTS.md`：项目内 Codex 执行约束。
- `CHART_SPEC.md`：图表视觉规则、内容系列规则、生成 prompt 模板。
- `PROJECT_SPEC.md`：工程架构、数据契约、缓存契约和模板契约。
- `TEMPLATE_SPEC.md`：周期性模板规划。
- `docs/STRATEGY.md`：账号定位和内容策略。
- `docs/观点库.md`：选题和观点库。
- `docs/DATA_SOURCES.md`：数据源说明。
