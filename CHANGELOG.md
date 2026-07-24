# Changelog

本文件记录 alpha-jerry 的所有显著变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 修复

- `total_mv`/`circ_mv`（万元）与 `float_share`（万股）双重数量级 bug：原始值已为「万」（Tushare 文档标注），原 `format_value` 又除 1万 得「万」造成 `37.14万`（实为 37.14亿）。新增 `_RAW_WAN_FIELDS`，这些字段按「万→亿」除以 1e4 换算（>=1e4 显示亿，否则原值），表头去掉冗余 `(万元)`；数据来源 CSV 的「单位」列仍记录原始单位万元/万股（文档）

- 采集 `end_date`（财报所属期间）被覆盖 bug：`fetch_financials` 此前按接口顺序 `data.update()`，`pledge_stat`/`fina_audit` 的 `end_date`（质押统计截止日/审计对应年报）覆盖了 income 的报告期，导致 CSV「报告期」列出现 `20260717` 等非季末日期。现锁定 `end_date` 为 income 的报告期，其余接口 `exclude={"end_date"}` 不覆盖（`_clean_record` 增 `exclude` 参数）。实测 5 股 `end_date` 由 `20260717/20250117/20251231` 修正为统一的 `20260331`（2026 一季报）
- `period=None`（"最新"）缓存永不刷新问题：`Cache` 增 `ttl_seconds`，仅对 `period=None` 条目按文件 mtime 判定过期；新增 `Settings.cache_ttl_hours`（默认 24h，0=永不过期）与 `.env.example` 的 `CACHE_TTL_HOURS`；显式 period 历史数据不可变，不受 TTL 约束

### 新增

- 数据来源 CSV（`YYMMDD-数据来源.csv`）增「单位」「单位来源」两列：`_DOCUMENTED_UNITS`/`_INFERRED_UNITS` 区分 Tushare 文档标注（仅 `total_mv`/`circ_mv` 万元、`float_share` 万股）与按财务惯例推断（元/%/倍/次等），单位可追溯
- 最新报告期校验工具（确保采集数据为最新）：
  - `src/utils/period.py`：纯函数 `expected_latest_period(today)`，按法定披露截止日（Q1→4-30、半年报→8-31、Q3→10-31、年报→次年4-30）推算今天理应已披露的最新报告期
  - `tests/test_period.py`：10 项边界单测（各截止日当天/前一天、跨年）
  - `scripts/verify_latest.py`：读 `data/test/YYMMDD.csv`，对每只股独立重查 `income_vip`(max end_date) / `daily_basic`(max trade_date) 与 CSV 比对，并校验 `end_date ≥ 预期最新报告期`；不读缓存，直接对质 Tushare
  - `integrated_tests/test_latest_period.py`：`@pytest.mark.network` 交叉校验测试（本地 `uv run pytest -m network -k latest`）
- M1 Step 1.4 冒烟测试增强（owner 决策，对 `integrated_tests/test_smoke_collect.py` 的修改意见）：
  - 数据来源 CSV 中 `ts_code` 归属 `stock_basic` 接口（原被 `income` 覆写，改为首个接口优先）
  - 冒烟特征 CSV 已实现 CJK 感知列对齐（单元格按字段值与列名显示宽度自动填充，无需手动调整）
- M1 Step 1.1 接口注册表：`src/data/interfaces.py`（`TUSHARE_INTERFACES`，20 个 5000 积分可调用接口，优先 vip 高级接口，含文档 URL / 积分要求 / 描述；`get_vip_api_name()` / `get_doc_url()` 辅助函数）
- M1 Step 1.1 字段对应表 CSV：`docs/field-mapping.csv`（68 行，55 需求字段 + 13 补充字段，含真实字段名 / 中文翻译 / 来源接口 / 文档 URL / 积分要求 / 对齐类型 / 用途）与生成脚本 `scripts/gen_field_mapping.py`
- M1 Step 1.1 字段契约文档：`docs/data-contract.md`（接口清单 / 字段对齐总览 / 计算型字段口径 / 百分比字段 / 不可用字段说明）— 已合并入 `docs/dev-guide.md` §8.1
- M1 Step 1.1 补充字段：`SUPPLEMENTARY_FIELDS`（13 个一票否决/评分辅助字段：money_cap/fin_exp_int_inc/audit_result/audit_agency/pledge_ratio/free_cashflow/inv_turn/pe_ttm/pb/dv_ttm/cash_div/total_mv/circ_mv）+ `SUPPLEMENTARY_COLUMNS` / `ALL_OUTPUT_COLUMNS`
- M1 Step 1.1 `REQUIREMENT_ALIGNMENT` 增补 `chinese_name` 字段（真实字段中文翻译）
- M0 Step 0.4 CI 门禁：`.github/workflows/ci.yml`（ruff check + ruff format 检查 + pytest，跳过 network 测试）
- M0 Step 0.4 骨架测试：`tests/test_skeleton.py`（Settings 导入/单例/默认值、data_path 创建子目录、DATA_SUBDIRS 映射、main 入口）
- M1 Step 1.1 数据源抽象与字段模型：`src/data/base.py`（BaseFetcher 抽象接口，主键用 ts_code）、`src/schemas/financial.py`（55 字段 Pydantic 模型 + 中英文 alias + 百分比字段集）、`tests/test_schemas.py`（字段表对齐、alias 双向、抽象类不可实例化）
- 修订 Step 1.1 字段溯源对齐 Tushare 官方文档：新增 `TUSHARE_FIELD_MAP` 记录每个 §8.1 字段的来源接口/真实字段名/取数方式（direct/computed/unavailable）；`FinancialFeatures`/`StockInfo` 增补 `ts_code` 主键；标注 5 个 Tushare 无直接对应字段（调整后每股净资产/A股数量/B股数量/国家持股/国有法人持股）与 8 个计算字段
- 显式声明 `lxml` 为直接依赖（tushare 运行前提，原为间接依赖未钉版本）
- 修订采集输出策略（owner 决策）：采集落地文件改用 Tushare 真实字段名 + 真实数据，不再使用 §8.1 中文字段名；`src/schemas/financial.py` 重写为 `StockFeatures`（46 个 Tushare 真实字段列）+ `REQUIREMENT_ALIGNMENT`（§8.1 55 需求→Tushare 字段对齐：exact 40 / approximate 4 / computed_in_scoring 6 / unavailable 5）；计算型需求字段不在采集层存储，改由 M2 评分纯函数计算。注：此与 dev-guide §8.1/FR-DATA-08 的中文字段名约定有偏离，业主要求以 Tushare 真实字段为准
- 项目设计文档：`docs/brd.md`、`docs/brd-1.md`、`docs/prd.md`、`docs/dev-guide.md`、`docs/ROADMAP.md`、`docs/dev-log.md`
- 工程基线：`.gitignore`、`.gitattributes`、`README.md`、`CHANGELOG.md`
- M0 工程骨架（进行中，见 [ROADMAP](docs/ROADMAP.md)）

### 变更

- M1 Step 1.4 采集输出收窄（owner 决策，偏离 dev-guide §8.1 / brd-1.md §7.8 业务基线，记录于此待业务评审）：
  - 删除 `dividend` 接口调用与 `DIVIDEND_FIELDS` / `cash_div` / `div_proc` 输出列
  - 删除 `上市日期(list_date)` / `公告日期(ann_date)` / `财务费用利息收入(fin_exp_int_inc)` 三列（含 `StockFeatures` / `StockInfo` 字段、各接口请求字段集、`REQUIREMENT_ALIGNMENT` 对齐条目）
  - 需求字段对齐表由 55 收敛为 53（exact 40→38），补充字段由 13 收敛为 11
  - `fetch_financials` 调用接口由 8 个减为 7 个
  - **影响提示**：§8.2 一票否决 "造假嫌疑" 中 "利息收入极低" 判定失去 `fin_exp_int_inc` 数据支撑，需 owner 后续确定替代信号或恢复该字段
  - brd-1.md §7.8（业务基线 55 字段清单）保持不变，仅在采集层落地时收窄
- 修订 Step 1.1 采集接口升级为 5000 积分 vip 优先策略：财务三表/指标/预告/快报/主营构成使用 `_vip` 后缀接口（按 period 批量取全市场）；`OUTPUT_COLUMNS` 从 46 列扩充至 55 列（新增 fin_exp_int_inc/money_cap/free_cashflow/inv_turn/pe_ttm/pb/dv_ttm/total_mv/circ_mv）；`PERCENT_FIELDS` 新增 `dv_ttm`；`StockFeatures` 新增 13 个补充字段；`tests/test_schemas.py` 新增接口注册表/vip 接口/补充字段/中文翻译等 10 项测试（共 21 项）
- 同步更新 `docs/dev-guide.md` §8.1（接口选型/vip 优先/补充字段/字段对应表 CSV）与 `docs/ROADMAP.md` Step 1.1/1.2（涉及文件/ vip 接口说明）
- **全项目落地文件格式由 xlsx 改为 csv**（owner 决策，Step 1.4 起）：所有 `data/` 下产物（`YYMMDD.csv` / `-评分.csv` / `-评级.csv` / `-否决.csv` / `-失败.csv` / `-荐股.csv` / 持仓 `.csv` / 热点 `.csv` 等）统一为 CSV；`src/core/pipeline.py` 失败清单改用 `csv` 标准库写入（移除 `openpyxl` 依赖）；新增 `src/reports/csv_writer.py`（中文列头 + 百分比带% + 大数亿/万 + CJK 对齐 + 数据来源表）；同步修订 `docs/dev-guide.md` §8（RIGID 业务规则文件名）/ §7.1（`save_xlsx`→`save_csv`）/ §5 目录树、`docs/prd.md`、`docs/brd.md`、`docs/brd-1.md`、`docs/ROADMAP.md`、`AGENTS.md` 中所有 xlsx 引用为 csv

## 版本规划

- `0.1.0` — M0 工程骨架（目录/AGENTS.md/pyproject/Settings/CI）
- `0.2.0` — M1 数据采集（Tushare 适配 + 特征字段落地）
- `0.3.0` — M2 评分评级（纯函数 + 单测 + 行业权重 + 否决）
- `0.4.0` — M3 报告输出（荐股 Top20 + 持仓表）
