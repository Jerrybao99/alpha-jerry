---
tags: [prd, 规格说明]
status: draft
version: 0.1.0
date: 2026-07-21
关联文档: [brd.md](./brd.md), [dev-log.md](./dev-log.md)
---

# alpha-jerry 产品需求文档（PRD）

> 本文件是 `alpha-jerry` 的产品规格说明（PRD），由 [brd.md](./brd.md) 衍生，结合工程规范文档（`coding.md` / `AGENTS.md.md`）、规范仓库（`qtcloud-devops` / `qtcloud-course`）、架构灵感范例（`openclaw`）与功能实现灵感范例（`OpenBB` / `daily_stock_analysis` / `Vibe-Trading` / `TradingAgents-CN`）共同确定。
>
> 当本文件与代码现状不一致时，以实际可执行内容为准并顺手修正文档，避免规则漂移。

---

## 0. 文档约定

- 本项目为中文项目，文档、注释、日志、Prompt 文案以中文为主，金融字段名同时给出中文与英文缩写。
- 评分与评级规则、字段清单、阈值表来自 BRD，是**不可漂移的刚性契约**；实现时必须在纯函数层加单元测试对齐文档约定（参考 `qtcloud-devops/AGENTS.md` 第 9 条）。
- 需求编号规则：`FR-<域>-<序号>`（Functional Requirement），`NFR-<序号>`（Non-Functional），`AR-<序号>`（Agent Requirement）。
- 优先级：`P0` 必须有 / `P1` 应该有 / `P2` 可以有。

---

## 1. 项目概述

### 1.1 项目定位

`alpha-jerry` 是一套**面向 A 股基本面分析的 AI Native 工具集**，覆盖"数据采集 → 评分 → 评级 → 报告 → 持仓监控 → 推送"完整工作流，帮助个人投资者识别优质公司并持续监控持仓风险。

它不是套壳聊天机器人，而是一个具备**多 Agent 编排、RAG 知识库、路由、工具、记忆、监控、反馈**的本地优先（local-first）企业级工程。

### 1.2 核心目标

| 目标 | 说明 |
|---|---|
| 工作流完整 | 落地 BRD 中 step1~step4 与"其他功能"全部能力 |
| AI Native | 评分/评级/点评由规则引擎 + LLM 协同，热点由 LLM 识别，对话由多 Agent 编排 |
| 简洁稳定 | 架构主流、先进、可扩展；遵循 `coding.md` 的 Easy Code 原则 |
| 本地优先 | 数据本地存储，不上传云端，保护隐私 |
| 双端可用 | Win / Mac 双端桌面 UI，随时自由对话交互 |
| 低成本 | 使用成熟开源工具与 DeepSeek 作为默认 LLM |

### 1.3 目标用户

- **程序开发小白 / 个人投资者**：需要一个"开箱即用、自然语言交互、自动跑流程"的 A 股基本面助手。
- 非目标用户：机构量化团队、高频交易者、需要云端多人协作的团队。

### 1.4 不做什么（Out of Scope）

- 不做量化高频交易、不做实时盘中下单交易执行。
- 不做多市场（港股/美股）——首版仅 A 股；架构预留扩展位。
- 不做云端 SaaS、不做多租户。
- 不做技术面短线策略（BRD 聚焦基本面）。

---

## 2. 技术栈与架构原则

### 2.1 技术栈（精确到主版本）

| 层 | 选型 | 版本约束 | 说明 |
|---|---|---|---|
| 语言 | Python | >= 3.12 | 后端/Agent/数据管道 |
| 包管理 | uv | latest | 单虚拟环境，锁文件 `uv.lock`（参考 `qtcloud-course`） |
| LLM | DeepSeek V4 Pro | 默认 provider | 通过 OpenAI 兼容接口接入 |
| UI 设计参考 | Kimi K3 | — | 设计稿生成参考 |
| 数据源 | Tushare Pro | latest | A 股基本面/行情/资金面 |
| Agent 框架 | LangGraph | 0.2+ | 多 Agent 编排、状态机、条件路由 |
| LLM 抽象 | LiteLLM / OpenAI SDK | latest | 统一 provider，便于切换 |
| RAG 向量库 | ChromaDB | latest | 本地嵌入向量存储 |
| 嵌入模型 | bge-small-zh（本地） | — | 中文金融语义，离线可跑 |
| 后端 API | FastAPI | 0.110+ | 桌面端与调度服务调用 |
| 调度 | APScheduler / 系统 cron | latest | 定时任务 |
| 数据处理 | pandas / openpyxl | latest | xlsx 读写 |
| 桌面端 | Electron + React（参考 openclaw apps） | — | Win/Mac 双端，套壳本地 FastAPI |
| 配置 | pydantic-settings + `.env` | latest | `Settings` 类集中管理 |
| 测试 | pytest | >= 8 | 单元 + 集成 |
| Lint/Format | ruff | latest | 统一格式 |

> 技术栈遵循"成熟、开源、低成本"约束；任何替换须在 ADR（架构决策记录）中说明。

### 2.2 架构原则（来源：`coding.md` + `openclaw` + `daily_stock_analysis`）

1. **目录边界清晰**：后端逻辑与数据源适配均在 `src/`（`src/data/` 放数据源适配），API 在 `api/`，桌面端在 `apps/desktop/`，部署在 `scripts/` 与 `manifests/`。
2. **配置抽离**：路径、超时、模型参数、API Key 全部走 `Settings`，禁止硬编码。
3. **数据源单一真源 + Fallback**：固定 Tushare 为主，预留适配器接口（参考 `daily_stock_analysis/data_provider` 的 `base.py` + 多 fetcher）。
4. **纯逻辑与 I/O 分层**：评分/评级/权重计算为纯函数，单独单测；爬取/写盘为 I/O 层，集成测试覆盖（`qtcloud-devops/AGENTS.md` 第 3、8、9 条）。
5. **Agent 不套壳**：有路由、有工具、有记忆、有监控、有反馈（BRD 需求 4）。
6. **本地优先**：向量库、数据库、缓存全部本地；除 LLM 推理外不外联。
7. **单 PR 单功能**：遵循 `coding.md` 交付标准，单 PR ≤ 20 文件。
8. **插件化扩展**：参考 openclaw，核心精简，可选能力（推送渠道、数据源）以扩展形式接入。

### 2.3 仓库目录结构

```
alpha-jerry/
├── AGENTS.md                  # 项目级 AI 行为规范（上下文入口）
├── README.md                  # 项目说明
├── CHANGELOG.md               # Keep a Changelog，SemVer
├── pyproject.toml             # 依赖与工具配置
├── uv.lock
├── .env.example               # 配置样板（新增配置项必须同步）
├── .gitignore
├── docs/                      # 文档
│   ├── brd.md
│   ├── prd.md                 # 本文件
│   ├── dev-log.md
│   ├── architecture.md        # 架构详解（ADR）
│   ├── data-contract.md       # 字段契约与评分规则
│   └── prompt-library.md      # Prompt 模板库
├── data/                      # 运行期数据（gitignore）
│   ├── fin/                   # YYMMDD.xlsx / -评分 / -评级 / -否决 / -失败
│   ├── analysis/              # YYMMDD-荐股.xlsx
│   ├── hold/                  # YYMMDD.xlsx / -09 / -17
│   ├── hot/                   # 热搜缓存与识别结果
│   ├── monitor/               # Agent 执行链
│   ├── feedback/              # 用户反馈
│   └── rag/                   # 向量库与知识库
├── src/                       # 源代码
│   ├── config.py              # Settings 入口
│   ├── core/                  # 主流程编排（pipeline）
│   ├── scoring/               # 评分纯逻辑（成长/稳健/回报/权重）
│   ├── rating/                # 评级与公司类型/行业分类
│   ├── reports/               # 报告生成（荐股/持仓/推送）
│   ├── agents/                # 多 Agent 定义与编排
│   ├── rag/                   # 知识库构建与检索
│   ├── notifications/         # 推送（邮件/微信）
│   ├── scheduler/             # 定时任务
│   ├── schemas/               # 数据结构/Pydantic 模型
│   ├── data/                  # 数据源适配（Tushare 主 + 适配器接口）
│   └── utils/
├── api/                       # FastAPI 路由
├── apps/
│   └── desktop/               # Electron + React 桌面端
├── scripts/                   # 辅助脚本（采集/初始化/打包）
├── tests/                     # 单元测试
├── integrated_tests/          # 集成测试
└── manifests/                 # 部署清单（Win/Mac 打包配置）
```

> 说明：BRD 中数据目录写作 `DATA/`，本 PRD 统一为小写 `data/` 以符合 `coding.md` 目录规范；子目录采用英文简写（`fin`/`analysis`/`hold`/`hot`/`monitor`/`feedback`/`rag`），文件名后缀（如 `-评分`/`-评级`/`-荐股`）保留中文以匹配 BRD 文案。

---

## 3. 系统架构

### 3.1 总体架构

系统分四层 + 一个桌面端外壳：

```
┌─────────────────────────────────────────────────────────────┐
│  Desktop Shell (Electron + React, Win/Mac)                   │
│  ─ 对话交互 / 报告查看 / 持仓录入 / 推送预览                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/SSE (localhost)
┌──────────────────────────┴──────────────────────────────────┐
│  API Layer (FastAPI)                                         │
│  ─ /chat /report /portfolio /hotspot /pipeline /health       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│  Agent Orchestration (LangGraph)                             │
│  ─ Router → DataAgent / ScoringAgent / RatingAgent /         │
│    ReportAgent / HotspotAgent / PortfolioAgent / ChatAgent   │
│  ─ Memory / RAG / Tools / Feedback / Monitor                 │
└──────────┬────────────────────────┬──────────────────────────┘
           │                        │
┌──────────┴───────────┐  ┌─────────┴────────────────────────┐
│  Domain Core (纯逻辑) │  │  Data Provider (I/O)             │
│  scoring/rating/      │  │  Tushare 适配器 / 缓存 / 重试     │
│  reports/schemas      │  │  RAG 检索 / 通知发送              │
└──────────────────────┘  └──────────────────────────────────┘
```

### 3.2 多 Agent 架构（AR）

参考 `TradingAgents-CN` 的 analysts/managers/researchers 分层与 `openclaw` 的 agent-core 抽象，设计如下 Agent 拓扑：

| Agent | 职责 | 工具 | 记忆 | 输出 |
|---|---|---|---|---|
| **RouterAgent** | 意图路由：对话/采集/评分/评级/报告/热点/持仓 | 意图分类器 | 短期会话 | 路由决策 |
| **DataAgent** | 采集全部 A 股并落地特征工程字段 | `fetch_all_stocks` / `fetch_financials` | 采集进度 | `data/fin/YYMMDD.xlsx` |
| **ScoringAgent** | 执行一票否决 + 三维评分 + 行业权重 + 综合分 | 调用 `scoring` 纯函数 | 评分快照 | `-评分.xlsx` |
| **RatingAgent** | 评级 + 公司类型 + 行业分类 + AI 点评 | 调用 `rating` 纯函数 + LLM 点评 | 评级历史 | `-评级.xlsx` |
| **ReportAgent** | 生成荐股 Top20 报告 + 持仓表 | `reports` 渲染 + LLM 亮点生成 | 报告索引 | `data/analysis/荐股.xlsx` / `data/hold/*.xlsx` |
| **HotspotAgent** | 采集热搜 → LLM 识别受益行业/个股 | `fetch_hot_search` / RAG 行业映射 | 热点时序 | `data/hot/` |
| **PortfolioAgent** | 持仓重算、风险高亮、趋势对比、操作建议 | 读取持仓 / 重算评分 / 对比 | 持仓变化 | `data/hold/YYMMDD-09.xlsx` 等 |
| **ChatAgent** | 自由对话，调用其他 Agent 工具回应用户 | 全部工具（受权限约束） | 长期会话 + RAG | 对话回复 |

编排要点（来源 BRD 需求 4 + 灵感范例）：

- **路由**：RouterAgent 基于 LLM 意图分类 + 规则兜底，分发到对应 Agent（参考 `TradingAgents-CN/graph/conditional_logic.py`）。
- **工具**：每个 Agent 的能力封装为 LangGraph ToolNode；纯逻辑工具（评分/评级）不依赖网络，可离线单测。
- **记忆**：分层记忆——短期会话记忆（对话上下文）、长期记忆（评分历史、持仓变化）、RAG 记忆（行业知识、规则文档）。
- **RAG 知识库**：将行业对照表、否决规则、评分阈值、行业分类逻辑入库，Agent 决策时检索对齐，避免幻觉漂移。
- **反馈**：用户可对点评/建议点赞或修正，写入反馈库，用于 Prompt 迭代与评分校准。
- **监控**：每次 Agent 执行记录 token 消耗、耗时、工具调用链、失败原因，落盘 `data/monitor/`，UI 可查。
- **反思**：参考 `TradingAgents-CN/graph/reflection.py`，关键决策（如荐股 Top20）支持一轮自我审查。

---

## 4. 功能需求

### 4.1 FR-DATA 数据采集与处理（BRD step 1）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-DATA-01 | 固定使用 Tushare Pro 作为唯一数据源，封装 `TushareFetcher`；预留 `BaseFetcher` 抽象，便于未来扩展同花顺等 | P0 |
| FR-DATA-02 | 读取全部 A 股上市公司清单（股票代码、名称、行业、上市日期） | P0 |
| FR-DATA-03 | 按特征工程字段表（见 §6.1）爬取所需数据，落地 `data/fin/YYMMDD.xlsx` | P0 |
| FR-DATA-04 | 采用最新报告期的三表数据（dev-log 已定） | P0 |
| FR-DATA-05 | 高速采集：并发受控（低并发线程池，参考 `daily_stock_analysis/main.py`），单股失败不影响整体，全量失败可续采 | P0 |
| FR-DATA-06 | 缓存与性能策略：按 `股票代码+报告期` 缓存原始响应，季度内增量更新，避免重复调用消耗积分 | P0 |
| FR-DATA-07 | Tushare 积分限流与重试：指数退避 + 限流器，超限降级提示用户 | P0 |
| FR-DATA-08 | 字段对齐：xlsx 列名采用 Tushare 接口真实返回字段名（§8.1，owner 决策），百分比字段保留两位小数并带百分号后缀 | P0 |
| FR-DATA-09 | 数值格式：替换科学计数法，用汉字表达数量级并保留两位小数（dev-log 已定） | P1 |
| FR-DATA-10 | 增量更新：季度财报季后更新基本面；每月更新资金面（BRD 更新章节） | P0 |

### 4.2 FR-SCORE 个股评分（BRD step 2）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-SCORE-01 | 一票否决：造假嫌疑 / 行业毁灭 / 诚信问题三项判定，触发即剔除评级（规则见 §6.2） | P0 |
| FR-SCORE-02 | 成长性得分 1-10，按营收增速/净利增速/盈利质量/现金流匹配四维判定（§6.3） | P0 |
| FR-SCORE-03 | 稳健性得分 1-10，按资产负债率/流动比率/存货周转率/审计意见判定（§6.3） | P0 |
| FR-SCORE-04 | 资金回报得分 1-10，按 ROE/自由现金流/分红率/估值判定（§6.3） | P0 |
| FR-SCORE-05 | 行业权重：按五类行业对照表（周期资源/大消费/证券金融/新能源制造/公用事业基建）取权重（§6.4） | P0 |
| FR-SCORE-06 | 综合分 = 成长分×成长权重 + 稳健分×稳健权重 + 回报分×回报权重，保留 1 位小数 | P0 |
| FR-SCORE-07 | 将综合分追加到原 xlsx 字段末尾，另存 `data/fin/YYMMDD-评分.xlsx`，保留全部原始字段 | P0 |
| FR-SCORE-08 | 评分逻辑为纯函数，无 I/O，单测覆盖全部阈值分支与边界值 | P0 |
| FR-SCORE-09 | 公司类型识别（千里马/现金牛/护城河）影响权重微调（§6.5） | P1 |

### 4.3 FR-RATE 个股评级（BRD step 3）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-RATE-01 | 基于综合分评级：8.5-10 👑皇冠明珠 / 7.0-8.4 ⭐优秀白马 / 5.5-6.9 🔄鸡肋·观察 / <5.5 ⚠️垃圾 | P0 |
| FR-RATE-02 | 评级字段追加到原 xlsx 末尾，另存 `data/fin/YYMMDD-评级.xlsx`，保留原字段 | P0 |
| FR-RATE-03 | 一票否决剔除的公司不出现在评级文件中，但记录到 `data/fin/YYMMDD-否决.xlsx` 供审计 | P0 |
| FR-RATE-04 | 评级为纯函数，单测覆盖区间边界（8.5/7.0/5.5） | P0 |

### 4.4 FR-REPORT 报告输出（BRD step 4）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-REPORT-01 | 按综合分降序取 Top20，输出荐股表，字段见 §6.6 | P0 |
| FR-REPORT-02 | 核心亮点由 AI 生成（≤30 字），点评由 AI 生成（≤50 字） | P0 |
| FR-REPORT-03 | 公司类型与行业分类由规则 + LLM 校验确定（§6.5） | P0 |
| FR-REPORT-04 | 操作建议与仓位建议按评级映射（§6.7） | P0 |
| FR-REPORT-05 | 落地 `data/analysis/YYMMDD-荐股.xlsx` | P0 |
| FR-REPORT-06 | 用户通过对话录入持仓（股票代码+名称），系统生成持仓表 `data/hold/YYMMDD.xlsx`，字段同荐股表 | P0 |
| FR-REPORT-07 | 荐股报告与持仓表均含评级 emoji 与中文评级名 | P0 |

### 4.5 FR-HOTSPOT 热点追踪（BRD 其他功能）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-HOTSPOT-01 | 每日 09:00 与 17:00 自动执行 | P0 |
| FR-HOTSPOT-02 | 采集当日前 10 热搜（百度/微博/东财），来源可配置 | P0 |
| FR-HOTSPOT-03 | 通过关键词匹配 + LLM 识别潜在市场机会与受益行业 | P0 |
| FR-HOTSPOT-04 | 受益行业经 RAG 映射到个股，输出 Top5 推荐 | P1 |
| FR-HOTSPOT-05 | 热点结果落盘 `data/hot/YYMMDD-HH.xlsx` 并入推送 | P0 |

### 4.6 FR-PORT 持股分析（BRD 其他功能）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-PORT-01 | 每日 09:00 与 17:00 自动执行 | P0 |
| FR-PORT-02 | 读取 `data/hold/YYMMDD.xlsx`，重爬重算各持仓字段，输出 `YYMMDD-09.xlsx` / `YYMMDD-17.xlsx` | P0 |
| FR-PORT-03 | 触发一票否决即高亮风险提醒 | P0 |
| FR-PORT-04 | 对比上次评分输出变化趋势（成长/稳健/回报/综合分差值） | P0 |
| FR-PORT-05 | 生成操作建议：持有/加仓/减仓/止损，规则可配置 | P0 |

### 4.7 FR-PUSH 推送（BRD 其他功能）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-PUSH-01 | 热点追踪与持股分析结束后立即推送 | P0 |
| FR-PUSH-02 | 内容：持仓分析摘要（含风险提示）+ 热点推荐 Top5 | P0 |
| FR-PUSH-03 | 邮件渠道：保留完整分析，HTML 表格渲染 | P0 |
| FR-PUSH-04 | 微信渠道（可选）：发送摘要 | P1 |
| FR-PUSH-05 | 单渠道失败不拖垮主流程（参考 `daily_stock_analysis` 稳定性护栏） | P0 |

### 4.8 FR-CHAT 对话交互（BRD 需求 8）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-CHAT-01 | Win/Mac 桌面端可随时自由对话交互（参考 openclaw） | P0 |
| FR-CHAT-02 | 对话可触发任意 Agent 工作流（如"跑一下今天评分""分析我的持仓"） | P0 |
| FR-CHAT-03 | 对话支持流式输出（SSE） | P1 |
| FR-CHAT-04 | 对话引用 RAG 知识库作答（评分规则、行业逻辑） | P0 |
| FR-CHAT-05 | 对话历史本地持久化，跨会话保留 | P0 |

### 4.9 FR-UI 桌面端 UI（BRD 需求 7/8/9）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-UI-01 | UI 设计稿参考 Kimi K3 风格生成，交互参考 openclaw 桌面端 | P0 |
| FR-UI-02 | 应用图标：巧克力色荷兰侏儒兔风格，类似 openclaw 图标质感 | P0 |
| FR-UI-03 | 主界面：对话区 + 报告区 + 持仓区 + 热点区 + 监控区 | P0 |
| FR-UI-04 | 报告区可查看荐股/持仓/热点 xlsx 渲染表格 | P0 |
| FR-UI-05 | 持仓区支持录入/编辑持仓，触发 PortfolioAgent | P0 |
| FR-UI-06 | Win/Mac 双端打包（manifests/ 提供打包配置） | P0 |
| FR-UI-07 | 数据本地化提示：UI 明示"数据本地存储，不上传云端" | P0 |

### 4.10 FR-UPDATE 数据更新（BRD 更新章节）

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-UPDATE-01 | 时间触发自动执行（调度器） | P0 |
| FR-UPDATE-02 | 每季度财报季后更新基本面数据 | P0 |
| FR-UPDATE-03 | 每月更新资金面数据 | P0 |
| FR-UPDATE-04 | 手动触发全量更新入口（CLI + UI） | P1 |

---

## 5. 非功能需求（NFR）

| 编号 | 维度 | 要求 |
|---|---|---|
| NFR-01 | 隐私 | 全部数据本地存储，不上传云端；仅 LLM 推理外联 DeepSeek，可配置本地模型替代 |
| NFR-02 | 双端兼容 | Win10+ / macOS 12+ 双端桌面端一致体验 |
| NFR-03 | 性能 | 全量 A 股采集（约 5000+ 只）在合理并发与限流下可在一晚完成；评分/评级纯函数毫秒级 |
| NFR-04 | 稳定性 | 单股/单源失败不拖垮整体；通知单渠道失败不拖垮主流程 |
| NFR-05 | 可观测 | Agent 执行链、token 消耗、耗时、失败原因落盘可查 |
| NFR-06 | 可扩展 | 数据源、推送渠道、Agent 均可插件式扩展 |
| NFR-07 | 配置化 | 路径/超时/模型/限流/阈值均可配置，禁止硬编码 |
| NFR-08 | 安全 | `.env` 不入库；`.env.example` 同步更新；Tushare token 等密钥不明文日志 |
| NFR-09 | 可测试 | 纯逻辑单测全覆盖；I/O 层集成测试覆盖；CI 阻断 lint/编译错误 |
| NFR-10 | 文档 | 字段契约、评分规则、Prompt、架构决策均有文档，与代码同步 |

---

## 6. 数据契约与规则（刚性，不可漂移）

### 6.1 特征工程字段表（BRD step 1）

采集并落地到 `data/fin/YYMMDD.xlsx`，**列名采用 Tushare 接口真实返回字段名、数据为真实值**（owner 决策，§8.1）。原始 55 需求字段→Tushare 真实字段的对齐表与 46 列输出清单的单一事实来源为代码：`src/schemas/financial.py` 的 `REQUIREMENT_ALIGNMENT` 与 `OUTPUT_COLUMNS`。对齐结果：exact 40 / approximate 4 / computed_in_scoring 6（评分时计算，不落盘）/ unavailable 5（首版不采集）。

> 完整字段清单与计算口径见 `docs/data-contract.md`（待创建）。涉及百分比的字段须带百分号后缀、保留两位小数（dev-log）。

### 6.2 一票否决规则

| 否决项 | 判定条件 |
|---|---|
| 造假嫌疑 | 货币资金高但利息收入极低；经营现金流连续多年远低于净利润 |
| 行业毁灭 | 技术路线被颠覆（如胶卷、燃油车零部件） |
| 诚信问题 | 频繁更换审计机构（3 年换 2 次以上）；大股东质押率 >70%；曾因信披违规被立案 |

### 6.3 三维评分阈值表

成长性 / 稳健性 / 资金回报各 1-10 分，阈值表见 BRD step 2 第 3/4/5 项。**实现时必须为每张阈值表编写纯函数单测，覆盖区间边界。**

### 6.4 行业权重对照表

五类行业（周期资源 / 大消费 / 证券金融 / 新能源制造 / 公用事业基建）的维度权重见 BRD step 2 第 6 项。权重以区间给出，实现时取区间中点为默认值，可在 `Settings` 中覆盖。

### 6.5 公司类型与行业分类（BRD step 4 第 2/3 项）

- 公司类型：🐎千里马 / 🐮现金牛 / 🛡️护城河，按典型特征判定并映射权重。
- 行业分类：周期资源 / 大消费 / 证券金融 / 新能源制造 / 公用事业基建，按典型公司与特殊情况判定。

### 6.6 荐股/持仓报告字段

| 字段（缩写） | 列属性 | 取值示例 |
|---|---|---|
| 股票代码（Code） | 文本 | 600000 |
| 股票名称（Name） | 文本 | 浦发银行 |
| 公司类型 | 文本 | 千里马/现金牛/护城河 |
| 行业分类 | 文本 | 周期资源/大消费/证券金融/新能源制造/公用事业基建 |
| 核心亮点 | 文本 | AI 生成，≤30 字 |
| 成长性 | 数值(1位) | 0-10 |
| 稳健性 | 数值(1位) | 0-10 |
| 回报性 | 数值(1位) | 0-10 |
| 综合分 | 数值(1位) | 0-10 |
| 评级 | 文本 | 皇冠明珠/优秀白马/鸡肋·观察/垃圾 |
| 点评 | 文本 | AI 点评，≤50 字 |

### 6.7 评级与操作建议映射

| 评级 | 操作建议 | 仓位建议 |
|---|---|---|
| 👑 皇冠明珠 | 重仓买入 | 10-20% |
| ⭐ 优秀白马 | 分批建仓 | 5-10% |
| 🔄 鸡肋·观察 | 观望/波段 | <3% |
| ⚠️ 垃圾 | 坚决回避 | 0% |

---

## 7. Agent 详细设计

> 本章为 `AR`（Agent Requirement）的展开，参考 `openclaw` agent-core 与 `TradingAgents-CN` agents 分层。

### 7.1 RouterAgent（路由）

- 输入：用户自然语言或定时触发信号。
- 职责：意图分类 → 分发到下游 Agent；无法识别时回退 ChatAgent。
- 工具：`classify_intent`（LLM + 规则正则兜底）。
- 约束：路由决策可解释、可日志回溯。

### 7.2 DataAgent（采集）

- 工具：`fetch_stock_list`、`fetch_financials(code, period)`、`save_xlsx`。
- 流程：读全量清单 → 并发受控采集 → 字段标准化 → 落地 `YYMMDD.xlsx`。
- 失败处理：单股失败记入 `data/fin/YYMMDD-失败.xlsx`，可续采。
- 反馈：采集进度通过 SSE 推送 UI。

### 7.3 ScoringAgent（评分）

- 工具：`run_veto`、`score_growth`、`score_stability`、`score_return`、`industry_weight`、`composite_score`（全部纯函数）。
- 流程：否决 → 三维评分 → 行业权重 → 综合分 → 追加字段 → 落地 `-评分.xlsx`。
- RAG：检索行业对照表确认权重，避免硬编码漂移。

### 7.4 RatingAgent（评级）

- 工具：`rate_by_score`（纯函数）、`llm_comment`（生成点评/亮点）。
- 流程：评级 → 公司类型/行业分类 → AI 点评/亮点 → 落地 `-评级.xlsx`。

### 7.5 ReportAgent（报告）

- 工具：`build_top20`、`render_portfolio`、`llm_highlight`。
- 流程：综合分降序取 Top20 → 渲染荐股表 → 生成持仓表。

### 7.6 HotspotAgent（热点）

- 工具：`fetch_hot_search`、`llm_identify_opportunity`、`rag_map_industry_to_stocks`。
- 流程：采热搜 → LLM 识别机会 → RAG 映射受益行业 → Top5 个股。

### 7.7 PortfolioAgent（持仓）

- 工具：`reload_holdings`、`rescore`、`diff_last_score`、`suggest_action`。
- 流程：重爬重算 → 风险高亮 → 趋势对比 → 操作建议。

### 7.8 ChatAgent（对话）

- 工具：可调用上述全部 Agent 的入口（受权限约束）。
- 记忆：短期会话 + 长期偏好 + RAG。
- 反馈：收集用户对回复的点赞/修正。

### 7.9 记忆与 RAG

- **短期记忆**：当前会话上下文（窗口可配）。
- **长期记忆**：评分历史、持仓变化、用户偏好（风险偏好、关注行业）。
- **RAG 知识库**：行业对照表、否决规则、评分阈值、行业分类逻辑、Prompt 模板。ChromaDB 本地存储，bge-small-zh 嵌入。

### 7.10 监控与反馈

- 每次 Agent 执行产出结构化记录：`agent_name / tools_called / tokens / latency / status / error`。
- UI 监控区可查看最近执行链。
- 用户反馈（点赞/修正）入 `data/feedback/`，用于 Prompt 与评分校准迭代。

---

## 8. 接口与 UI

### 8.1 FastAPI 路由（初版）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/chat` | 对话入口（SSE 流式） |
| POST | `/pipeline/run` | 触发采集/评分/评级/报告全流程 |
| GET | `/report/{date}` | 获取荐股/持仓/热点报告 |
| POST | `/portfolio` | 录入/更新持仓 |
| GET | `/hotspot/{date}` | 获取热点分析 |
| GET | `/health` | 健康检查 |

### 8.2 桌面端（apps/desktop）

- 技术栈：Electron + React + Vite，套壳本地 FastAPI。
- 设计参考：openclaw 桌面端交互 + Kimi K3 视觉风格。
- 图标：巧克力色荷兰侏儒兔，提供 `.ico`（Win）与 `.icns`（Mac）。
- 双端打包：`manifests/` 提供 Win（nsis/portable）与 Mac（dmg）配置。

---

## 9. 配置与部署

### 9.1 配置项（`.env.example` 必须同步）

```
DEEPSEEK_API_KEY=        # LLM 密钥
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
TUSHARE_TOKEN=           # Tushare Pro token
DATA_DIR=data            # 数据根目录
CONCURRENCY=4            # 采集并发
TUSHARE_RATE_LIMIT=200   # 每分钟调用上限
HOTSPOT_CRON_09=0 9 * * *
HOTSPOT_CRON_17=0 17 * * *
PORTFOLIO_CRON_09=0 9 * * *
PORTFOLIO_CRON_17=0 17 * * *
SMTP_HOST= / SMTP_PORT= / SMTP_USER= / SMTP_PASS=
WECHAT_PUSH_ENABLED=false
LLM_LOCAL_FALLBACK=false  # 是否启用本地模型兜底
```

### 9.2 部署形态

- 本地运行：`python main.py` 或桌面端启动拉起 FastAPI。
- 定时任务：APScheduler 内嵌；亦可系统 cron。
- 打包：桌面端一键安装包（Win/Mac）。

---

## 10. 里程碑与交付

遵循 `coding.md` 交付标准：单 PR 单功能、≤20 文件、自测通过、PR 描述含目的/摘要/验证方式。

| 里程碑 | 范围 | 验收 |
|---|---|---|
| M0 工程骨架 | 目录、AGENTS.md、pyproject、Settings、CI（ruff+pytest） | `uv run pytest` 通过骨架用例 |
| M1 数据采集 | DataAgent + Tushare 适配 + 字段落地 | 随机 5 股（dev-log）采集成功，xlsx 字段齐全 |
| M2 评分评级 | 纯函数 + 单测 + 行业权重 + 否决 | 阈值表单测全覆盖；`-评分`/`-评级` xlsx 产出 |
| M3 报告输出 | 荐股 Top20 + 持仓表 + AI 点评 | `data/analysis/荐股.xlsx` 生成 |
| M4 多 Agent 编排 | RouterAgent + ChatAgent + LangGraph + 记忆/RAG | 对话可触发各 Agent |
| M5 热点 + 持仓监控 + 推送 | HotspotAgent + PortfolioAgent + 邮件/微信 | 定时任务与推送链路打通 |
| M6 桌面端 UI | Electron + React 双端 + 图标 + 打包 | Win/Mac 可安装运行 |
| M7 监控与反馈 | 执行链落盘 + UI 监控区 + 反馈库 | 监控可查、反馈可写 |

---

## 11. 风险与约束

| 风险 | 影响 | 缓解 |
|---|---|---|
| Tushare 积分/限流 | 采集被限 | 限流器 + 缓存 + 续采；积分不足时提示用户 |
| 数据源单一 | 单点故障 | 预留 `BaseFetcher` 抽象，后续接 akshare/同花顺 |
| LLM 幻觉 | 点评/亮点失真 | 关键决策走规则引擎；LLM 仅生成文案并由规则校验 |
| 财报口径变化 | 字段漂移 | 字段契约文档 + 集成测试用固定样本对齐 |
| 双端打包差异 | 体验不一致 | 共享 React UI，平台差异收敛到 `manifests/` |
| 隐私合规 | 数据外泄 | 本地优先；仅 LLM 推理外联，可切本地模型 |
| 法律风险 | 投资建议合规 | 明示"仅供参考，不构成投资建议"；免责声明（dev-log 待定项） |

---

## 12. 验收标准（DoD）

- [ ] BRD step1~step4 全流程可一键跑通并产出对应 xlsx。
- [ ] 评分/评级纯函数单测覆盖全部阈值边界。
- [ ] 一票否决剔除公司记录可审计。
- [ ] 热点/持仓定时任务按 09:00/17:00 触发并推送。
- [ ] 桌面端 Win/Mac 可安装运行，可对话交互。
- [ ] 图标为巧克力色荷兰侏政兔风格。
- [ ] 数据全部本地存储，`.env` 不入库。
- [ ] `docs/data-contract.md` / `docs/architecture.md` / `docs/prompt-library.md` 与代码同步。
- [ ] `CHANGELOG.md` 按 Keep a Changelog 维护，版本号遵循 SemVer。
- [ ] CI（ruff lint + pytest）通过。

---

## 13. 待定事项（来自 dev-log）

- [ ] 知识产权保护策略
- [ ] 法律风险与免责条款措辞
- [ ] 评审：昂哥、果哥、郑哥
- [ ] github 提交名规范
- [ ] 小红书收藏购物车（运营相关，非工程）
- [ ] "需求编程的 agent"——是否提供让用户用自然语言描述并生成新评分规则的 Agent（M6 后评估）

---

## 14. 参考资料

- 工程规范：`coding.md`、`AGENTS.md.md`
- 规范仓库：`qtcloud-devops-main`、`qtcloud-course-main`
- 架构灵感：`openclaw-main`（apps 桌面端、agent-core、extensions 插件、VISION）
- 功能灵感：`OpenBB-develop`（platform/extensions/providers 分层）、`daily_stock_analysis-main`（data_provider 多源 fallback、pipeline、AGENTS 治理）、`Vibe-Trading-main`（agent/cli/backtest）、`TradingAgents-CN-main`（agents 分层、graph 编排、reflection、dataflows）
