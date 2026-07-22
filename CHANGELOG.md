# Changelog

本文件记录 alpha-jerry 的所有显著变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- M0 Step 0.4 CI 门禁：`.github/workflows/ci.yml`（ruff check + ruff format 检查 + pytest，跳过 network 测试）
- M0 Step 0.4 骨架测试：`tests/test_skeleton.py`（Settings 导入/单例/默认值、data_path 创建子目录、DATA_SUBDIRS 映射、main 入口）
- M1 Step 1.1 数据源抽象与字段模型：`src/data/base.py`（BaseFetcher 抽象接口，主键用 ts_code）、`src/schemas/financial.py`（55 字段 Pydantic 模型 + 中英文 alias + 百分比字段集）、`tests/test_schemas.py`（字段表对齐、alias 双向、抽象类不可实例化）
- 修订 Step 1.1 字段溯源对齐 Tushare 官方文档：新增 `TUSHARE_FIELD_MAP` 记录每个 §8.1 字段的来源接口/真实字段名/取数方式（direct/computed/unavailable）；`FinancialFeatures`/`StockInfo` 增补 `ts_code` 主键；标注 5 个 Tushare 无直接对应字段（调整后每股净资产/A股数量/B股数量/国家持股/国有法人持股）与 8 个计算字段
- 显式声明 `lxml` 为直接依赖（tushare 运行前提，原为间接依赖未钉版本）
- 修订采集输出策略（owner 决策）：采集落地文件改用 Tushare 真实字段名 + 真实数据，不再使用 §8.1 中文字段名；`src/schemas/financial.py` 重写为 `StockFeatures`（46 个 Tushare 真实字段列）+ `REQUIREMENT_ALIGNMENT`（§8.1 55 需求→Tushare 字段对齐：exact 40 / approximate 4 / computed_in_scoring 6 / unavailable 5）；计算型需求字段不在采集层存储，改由 M2 评分纯函数计算。注：此与 dev-guide §8.1/FR-DATA-08 的中文字段名约定有偏离，业主要求以 Tushare 真实字段为准
- 项目设计文档：`docs/brd.md`、`docs/brd-1.md`、`docs/prd.md`、`docs/dev-guide.md`、`docs/ROADMAP.md`、`docs/dev-log.md`
- 工程基线：`.gitignore`、`.gitattributes`、`README.md`、`CHANGELOG.md`
- M0 工程骨架（进行中，见 [ROADMAP](docs/ROADMAP.md)）

## 版本规划

- `0.1.0` — M0 工程骨架（目录/AGENTS.md/pyproject/Settings/CI）
- `0.2.0` — M1 数据采集（Tushare 适配 + 特征字段落地）
- `0.3.0` — M2 评分评级（纯函数 + 单测 + 行业权重 + 否决）
- `0.4.0` — M3 报告输出（荐股 Top20 + 持仓表）
