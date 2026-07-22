# Changelog

本文件记录 alpha-jerry 的所有显著变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- M1 Step 1.1 接口注册表：`src/data/interfaces.py`（`TUSHARE_INTERFACES`，20 个 5000 积分可调用接口，优先 vip 高级接口，含文档 URL / 积分要求 / 描述；`get_vip_api_name()` / `get_doc_url()` 辅助函数）
- M1 Step 1.1 字段对应表 CSV：`docs/field-mapping.csv`（68 行，55 需求字段 + 13 补充字段，含真实字段名 / 中文翻译 / 来源接口 / 文档 URL / 积分要求 / 对齐类型 / 用途）与生成脚本 `scripts/gen_field_mapping.py`
- M1 Step 1.1 字段契约文档：`docs/data-contract.md`（接口清单 / 字段对齐总览 / 计算型字段口径 / 百分比字段 / 不可用字段说明）
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

- 修订 Step 1.1 采集接口升级为 5000 积分 vip 优先策略：财务三表/指标/预告/快报/主营构成使用 `_vip` 后缀接口（按 period 批量取全市场）；`OUTPUT_COLUMNS` 从 46 列扩充至 55 列（新增 fin_exp_int_inc/money_cap/free_cashflow/inv_turn/pe_ttm/pb/dv_ttm/total_mv/circ_mv）；`PERCENT_FIELDS` 新增 `dv_ttm`；`StockFeatures` 新增 13 个补充字段；`tests/test_schemas.py` 新增接口注册表/vip 接口/补充字段/中文翻译等 10 项测试（共 21 项）
- 同步更新 `docs/dev-guide.md` §8.1（接口选型/vip 优先/补充字段/字段对应表 CSV）与 `docs/ROADMAP.md` Step 1.1/1.2（涉及文件/ vip 接口说明）

## 版本规划

- `0.1.0` — M0 工程骨架（目录/AGENTS.md/pyproject/Settings/CI）
- `0.2.0` — M1 数据采集（Tushare 适配 + 特征字段落地）
- `0.3.0` — M2 评分评级（纯函数 + 单测 + 行业权重 + 否决）
- `0.4.0` — M3 报告输出（荐股 Top20 + 持仓表）
