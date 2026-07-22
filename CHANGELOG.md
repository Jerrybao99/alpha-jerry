# Changelog

本文件记录 alpha-jerry 的所有显著变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- M0 Step 0.4 CI 门禁：`.github/workflows/ci.yml`（ruff check + ruff format 检查 + pytest，跳过 network 测试）
- M0 Step 0.4 骨架测试：`tests/test_skeleton.py`（Settings 导入/单例/默认值、data_path 创建子目录、DATA_SUBDIRS 映射、main 入口）
- 项目设计文档：`docs/brd.md`、`docs/brd-1.md`、`docs/prd.md`、`docs/dev-guide.md`、`docs/ROADMAP.md`、`docs/dev-log.md`
- 工程基线：`.gitignore`、`.gitattributes`、`README.md`、`CHANGELOG.md`
- M0 工程骨架（进行中，见 [ROADMAP](docs/ROADMAP.md)）

## 版本规划

- `0.1.0` — M0 工程骨架（目录/AGENTS.md/pyproject/Settings/CI）
- `0.2.0` — M1 数据采集（Tushare 适配 + 特征字段落地）
- `0.3.0` — M2 评分评级（纯函数 + 单测 + 行业权重 + 否决）
- `0.4.0` — M3 报告输出（荐股 Top20 + 持仓表）
