---
tags: [roadmap, 路线图]
status: active
version: 1.1.0
date: 2026-07-21
依据: [dev-guide.md](./dev-guide.md) §9 功能需求清单 + §13 里程碑 + §12 验证门禁
---

# alpha-jerry 开发工程路线图（ROADMAP）

## M0 工程骨架

### Step 0.1 初始化仓库与基础文件

- [x] 在项目根目录初始化 git，创建 `.gitignore`、`README.md`、`CHANGELOG.md`。

### Step 0.2 依赖管理与工具配置

- **涉及文件**：`pyproject.toml`、`uv.lock`、`.env.example`
- [x] 用 `uv` 初始化 Python 项目，配置 `pyproject.toml`，加入 ruff（格式/检查）与 pytest（测试）。

### Step 0.3 目录骨架与配置入口

- **涉及文件**：`AGENTS.md`、`src/config.py`、`src/__init__.py`、各子目录 `__init__.py`、`main.py`、`.env.example`
- [x] 按 dev-guide §5 创建源码目录结构；写 `AGENTS.md`（项目级 AI 行为规范）；写 `src/config.py` 的 `Settings` 类雏形与 `.env.example`；建 `main.py` 作为运行入口（dev-guide §10.3）。

### Step 0.4 CI 门禁与第一个骨架测试

- **涉及文件**：`.github/workflows/ci.yml`、`tests/test_skeleton.py`
- [x] 加 GitHub Actions workflow（ruff + pytest），写一个最简单的骨架测试让 CI 有东西可跑。

## M1 数据采集

**目标**：能从 Tushare 采集 A 股财务数据并落地为 `data/fin/YYMMDD.xlsx`。
**需求覆盖**：BR-01/02 · FR-DATA-01~10 · FR-UPDATE-02/03（季度基本面/月度资金面更新）。

### Step 1.1 数据源抽象与字段模型

- **涉及文件**：`src/data/base.py`、`src/data/__init__.py`、`src/schemas/financial.py`
- [x] 在 `src/data/base.py` 定义 `BaseFetcher` 抽象接口（主键 `ts_code`）；在 `src/schemas/financial.py` 用 Pydantic 定义特征工程字段模型——字段名即 Tushare 真实字段名（`OUTPUT_COLUMNS` 46 列）+ `REQUIREMENT_ALIGNMENT`（§8.1 的 55 需求→Tushare 字段对齐表）。

- **断点提交**：
  ```bash
   src/data/base.py src/data/__init__.py src/schemas/financial.py
  git commit -m "feat(data): add base fetcher interface and field schemas"
  ```

### Step 1.2 Tushare 适配器与限流重试

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：实现 `src/data/tushare_fetcher.py`，含限流器（每分钟调用上限）与指数退避重试（FR-DATA-07）。
- **涉及文件**：`src/data/tushare_fetcher.py`
- **学习点**：Tushare 按积分限流，调用太快会被拒。**指数退避** = 失败后等 1s、2s、4s 再重试，是处理外部接口不稳定的标准手法。
- **验证**：写一个 `tests/test_tushare_fetcher.py`，mock 掉网络，测试限流与重试逻辑。
- **断点提交**：
  ```bash
  git add src/data/tushare_fetcher.py tests/test_tushare_fetcher.py
  git commit -m "feat(data): implement tushare fetcher with rate limit"
  ```

### Step 1.3 采集编排、缓存与失败隔离

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：在 `src/core/pipeline.py` 写采集主流程——读全量清单 → 低并发线程池采集 → 缓存原始响应 → 字段标准化；单股失败入 `data/fin/YYMMDD-失败.xlsx`。
- **涉及文件**：`src/core/pipeline.py`、`src/utils/cache.py`、`src/utils/format.py`
- **学习点**：
  - **低并发线程池**：A 股 5000+ 只，不能一次性全请求（会被限流），用线程池控制并发数（如 4）。
  - **缓存键 = 股票代码 + 报告期**：同一季度内重复跑不重复调接口，省积分（FR-DATA-06）。
  - **失败隔离**：一只股票出错不能拖垮整体，记下来后续采（FR-DATA-05）。
- **验证**：`uv run pytest tests/test_pipeline.py`（mock 数据源）。
- **断点提交**：
  ```bash
  git add src/core/pipeline.py src/utils/cache.py src/utils/format.py tests/test_pipeline.py
  git commit -m "feat(data): add collection pipeline with cache and failure isolation"
  ```

### Step 1.4 随机 5 股冒烟测试与 xlsx 落地

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：写脚本随机选 5 股真实采集，落地 `data/fin/YYMMDD.xlsx`；字段格式化（Tushare 真实字段名列头、百分比两位小数带后缀、替换科学计数法——§8.1）。
- **涉及文件**：`scripts/smoke_collect.py`、`src/reports/xlsx_writer.py`
- **关键命令**：
  ```bash
  uv run python scripts/smoke_collect.py --sample 5
  ```
- **学习点**：**冒烟测试** = 用最小代价验证主链路通不通。先用 5 股跑通，再上全量。集成测试（`integrated_tests/`）放需要真实网络的测试，单元测试（`tests/`）mock 掉网络。
- **验证**：打开生成的 xlsx，确认字段齐全、百分比格式正确。
- **断点提交**：
  ```bash
  git add scripts/smoke_collect.py src/reports/xlsx_writer.py integrated_tests/test_smoke_collect.py
  git commit -m "test(data): add 5-stock smoke test and xlsx output"
  ```

> 🎯 **M1 验收**：5 股冒烟通过，xlsx 字段对齐 dev-guide §8.1。每个断点提交后直接 `git push origin main`。

---

## M2 评分评级

**目标**：把 dev-guide §8 的业务规则（一票否决、三维评分、行业权重、综合分、评级）落地为纯函数 + 单测。
**验收**：阈值表单测全覆盖；`-评分`/`-评级` xlsx 产出。
**需求覆盖**：BR-03/04/05 · FR-SCORE-01~09 · FR-RATE-01~04。

### Step 2.1 三维评分纯函数 + 单测

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：在 `src/scoring/` 实现成长性/稳健性/资金回报三个评分纯函数（dev-guide §8.3），每个阈值表配单测覆盖区间边界。
- **涉及文件**：`src/scoring/growth.py`、`src/scoring/stability.py`、`src/scoring/return.py`、对应 `tests/test_scoring_*.py`
- **学习点**：**纯函数** = 给相同输入永远得相同输出，不碰网络/文件/时间。这种函数最好测、最不易出 bug。dev-guide §6.3 原则 4 要求评分必须纯函数。**边界值测试**：如 8.5、7.0、5.5 这些临界点最容易出错，必须专门测。
- **验证**：`uv run pytest tests/test_scoring_growth.py tests/test_scoring_stability.py tests/test_scoring_return.py`
- **断点提交**：
  ```bash
  git add src/scoring/growth.py src/scoring/stability.py src/scoring/return.py tests/test_scoring_*.py
  git commit -m "feat(scoring): add three-dimension scoring pure functions"
  ```

### Step 2.2 行业权重、综合分与一票否决

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：实现行业权重对照表（§8.4）、综合分公式（§8.5）、一票否决（§8.2）；否决记录入 `data/fin/YYMMDD-否决.xlsx`。
- **涉及文件**：`src/scoring/weights.py`、`src/scoring/composite.py`、`src/scoring/veto.py`、对应测试
- **学习点**：权重以区间给出时取中点为默认值，可被 `Settings` 覆盖（dev-guide §8.4 备注）。一票否决是"硬性风险"，触发即剔除但必须留审计记录（可追溯）。
- **验证**：`uv run pytest tests/test_scoring_weights.py tests/test_scoring_composite.py tests/test_scoring_veto.py`
- **断点提交**：
  ```bash
  git add src/scoring/weights.py src/scoring/composite.py src/scoring/veto.py tests/test_scoring_*.py
  git commit -m "feat(scoring): add industry weights, composite score and veto"
  ```

### Step 2.3 评级纯函数与边界单测

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：在 `src/rating/` 实现评级映射（§8.6），单测覆盖 8.5 / 7.0 / 5.5 三个临界值归属。
- **涉及文件**：`src/rating/rate.py`、`tests/test_rating_rate.py`
- **学习点**：`<5.5` 是垃圾、`5.5` 是鸡肋·观察——这种"等号归哪边"的细节最易写错，单测要明确断言。
- **验证**：`uv run pytest tests/test_rating_rate.py`
- **断点提交**：
  ```bash
  git add src/rating/rate.py tests/test_rating_rate.py
  git commit -m "feat(rating): add rating mapping with boundary tests"
  ```

### Step 2.4 评分评级串联 xlsx 落地

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：把评分与评级串进 pipeline，输出 `data/fin/YYMMDD-评分.xlsx` 与 `data/fin/YYMMDD-评级.xlsx`，保留全部原始字段（追加新列）。
- **涉及文件**：`src/core/pipeline.py`（扩展）、`src/reports/xlsx_writer.py`（扩展）
- **学习点**：**追加字段不破坏原字段**是数据契约的稳定性要求（dev-guide §15 决策优先级），下游消费方才不会突然崩。
- **验证**：用 M1 的 5 股样本跑全流程，检查两个 xlsx 生成且评级列正确。
- **断点提交**：
  ```bash
  git add src/core/pipeline.py src/reports/xlsx_writer.py integrated_tests/test_score_rate.py
  git commit -m "feat(rating): wire scoring and rating to xlsx output"
  ```

> 🎯 **M2 验收**：`uv run pytest` 全绿；5 股样本产出 `-评分`/`-评级`/`-否决` xlsx。每个断点提交后直接 `git push origin main`。

---

## M3 报告输出

**目标**：生成荐股 Top20 报告与持仓表，含 AI 亮点与点评。
**验收**：`data/analysis/YYMMDD-荐股.xlsx` 生成。
**需求覆盖**：BR-06/07 · FR-REPORT-01~07。

### Step 3.1 公司类型、行业分类与操作建议

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：实现公司类型（千里马/现金牛/护城河，§8.7）、行业分类（§8.8）、评级→操作建议映射（§8.9）。
- **涉及文件**：`src/rating/company_type.py`、`src/rating/industry.py`、`src/rating/advice.py`、对应测试
- **验证**：`uv run pytest tests/test_rating_*.py`
- **断点提交**：
  ```bash
  git add src/rating/company_type.py src/rating/industry.py src/rating/advice.py tests/test_rating_*.py
  git commit -m "feat(report): add company type, industry and advice mapping"
  ```

### Step 3.2 荐股 Top20 与持仓表生成

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：按综合分降序取 Top20，渲染荐股表（字段见 §8.10）；支持对话录入持仓生成 `data/hold/YYMMDD.xlsx`。
- **涉及文件**：`src/reports/picks.py`、`src/reports/portfolio.py`
- **学习点**：核心亮点（≤30 字）与点评（≤50 字）由 LLM 生成，但**关键决策走规则引擎**，LLM 只写文案并由规则校验（风险 R-04 缓解）。
- **验证**：5 股样本扩展到足够数量后生成荐股表；检查字段齐全。
- **断点提交**：
  ```bash
  git add src/reports/picks.py src/reports/portfolio.py integrated_tests/test_reports.py
  git commit -m "feat(report): generate top20 picks and portfolio table"
  ```

### Step 3.3 字段契约与 Prompt 文档

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：补 `docs/data-contract.md`（字段计算口径）与 `docs/prompt-library.md`（亮点/点评 Prompt 模板）。
- **涉及文件**：`docs/data-contract.md`、`docs/prompt-library.md`
- **学习点**：文档与代码同步是工程基本功（NFR-10）。字段口径写不清，下游（包括你自己三个月后）会反复踩坑。
- **验证**：人工核对字段口径与代码一致。
- **断点提交**：
  ```bash
  git add docs/data-contract.md docs/prompt-library.md
  git commit -m "docs: add data contract and prompt library"
  ```

> 🎯 **M3 验收**：step1~step4 全流程一键跑通并产出 xlsx（dev-guide §12.3 DoD 第 1 条）。每个断点提交后直接 `git push origin main`。

---

## M4 多 Agent 编排

**目标**：把单线 pipeline 升级为多 Agent 编排，支持自然语言对话驱动。
**验收**：对话可触发各 Agent。
**需求覆盖**：BR-12/14/17 · AR-*（§7）· FR-CHAT-01~05。

### Step 4.1 LLM 适配层与 DeepSeek 接入

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：在 `src/agents/llm_adapter.py` 封装 DeepSeek（OpenAI 兼容接口），统一 provider 接口，便于未来切换。
- **涉及文件**：`src/agents/llm_adapter.py`、`.env.example`（补 `DEEPSEEK_*`，对齐 §10.2）
- **学习点**：把 LLM 调用收进一个适配层，业务代码不直接依赖某家 SDK，换模型只改适配层（依赖倒置）。
- **验证**：写一个 mock 测试 + 一个真实调用冒烟（标 `@pytest.mark.network`，CI 不跑）。
- **断点提交**：
  ```bash
  git add src/agents/llm_adapter.py .env.example tests/test_llm_adapter.py
  git commit -m "feat(llm): add deepseek adapter"
  ```

### Step 4.2 RAG 知识库

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：用 ChromaDB + bge-small-zh 把行业对照表、否决规则、评分阈值、行业分类逻辑入库（dev-guide §7.2 RAG 要素）。
- **涉及文件**：`src/rag/store.py`、`src/rag/indexer.py`、`src/rag/retriever.py`
- **学习点**：RAG = 检索增强生成。Agent 决策前先检索知识库对齐规则，防止 LLM"幻觉"导致评分漂移。向量库本地存储，符合 local-first（NFR-01）。
- **验证**：`uv run pytest tests/test_rag_retriever.py`
- **断点提交**：
  ```bash
  git add src/rag/ tests/test_rag_retriever.py
  git commit -m "feat(rag): build local knowledge base"
  ```

### Step 4.3 RouterAgent 与 Agent 编排

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：用 LangGraph 实现 RouterAgent（意图路由 + 规则兜底）与各业务 Agent（Data/Scoring/Rating/Report），组装状态机（dev-guide §7.1）。
- **涉及文件**：`src/agents/router.py`、`src/agents/data_agent.py`、`src/agents/scoring_agent.py` 等、`src/agents/graph.py`
- **学习点**：**路由 = 意图分类 + 分发**。RouterAgent 先判断用户想干嘛（采集？评分？看报告？），再交给对应 Agent。无法识别时回退 ChatAgent。决策要可日志回溯。
- **验证**：`uv run pytest tests/test_agents_router.py`
- **断点提交**：
  ```bash
  git add src/agents/router.py src/agents/data_agent.py src/agents/scoring_agent.py src/agents/graph.py tests/test_agents_router.py
  git commit -m "feat(agents): add router and agent orchestration"
  ```

### Step 4.4 ChatAgent、记忆与流式对话 API

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：实现 ChatAgent + 分层记忆（短期会话/长期偏好/RAG）；加 `POST /chat`（SSE 流式，§11.1）。
- **涉及文件**：`src/agents/chat_agent.py`、`src/agents/memory.py`、`api/routes/chat.py`
- **学习点**：**SSE（Server-Sent Events）** 让对话"一个字一个字蹦出来"，体验远好于等整段返回。记忆分层让 Agent 跨会话记得你的持仓与偏好。
- **验证**：本地起服务，用 curl 测 `/chat` 能流式返回。
- **断点提交**：
  ```bash
  git add src/agents/chat_agent.py src/agents/memory.py api/routes/chat.py tests/test_chat.py
  git commit -m "feat(chat): add memory and streaming chat api"
  ```

> 🎯 **M4 验收**：自然语言可触发采集/评分/报告。每个断点提交后直接 `git push origin main`。

---

## M5 热点追踪 + 持股监控 + 推送

**目标**：每日 09:00/17:00 自动跑热点与持仓分析并推送。
**验收**：定时任务与推送链路打通。
**需求覆盖**：BR-08/09/10/11 · FR-HOTSPOT-01~05 · FR-PORT-01~05 · FR-PUSH-01~05 · FR-UPDATE-01。

### Step 5.1 定时调度器

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：用 APScheduler 实现 09:00/17:00 触发（dev-guide §10.2 cron 配置：`HOTSPOT_CRON_09`/`PORTFOLIO_CRON_09` 等）。
- **涉及文件**：`src/scheduler/scheduler.py`、`.env.example`（补 cron 配置，对齐 §10.2）
- **学习点**：cron 表达式 `0 9 * * *` = 每天 9 点。把触发时间放配置，不硬编码（NFR-07）。
- **验证**：把 cron 改成 1 分钟后触发，观察日志。
- **断点提交**：
  ```bash
  git add src/scheduler/ tests/test_scheduler.py
  git commit -m "feat(scheduler): add cron jobs for 09 and 17"
  ```

### Step 5.2 HotspotAgent 热点追踪

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：采 Top10 热搜（百度/微博/东财）→ LLM 识别受益行业 → RAG 映射个股 Top5，落 `data/hot/`。
- **涉及文件**：`src/agents/hotspot_agent.py`、`src/data/hot_search_fetcher.py`
- **学习点**：热搜来源不稳定，要多来源 fallback，单个失败不拖垮（风险 R-05）。
- **验证**：`uv run pytest tests/test_hotspot_agent.py`
- **断点提交**：
  ```bash
  git add src/agents/hotspot_agent.py src/data/hot_search_fetcher.py tests/test_hotspot_agent.py
  git commit -m "feat(hotspot): add hotspot tracking agent"
  ```

### Step 5.3 PortfolioAgent 持股监控

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：重爬重算持仓 → 风险高亮（一票否决触发）→ 趋势对比（与上次评分差值）→ 操作建议（持有/加仓/减仓/止损），输出 `data/hold/YYMMDD-09.xlsx`/`-17.xlsx`。
- **涉及文件**：`src/agents/portfolio_agent.py`
- **验证**：`uv run pytest tests/test_portfolio_agent.py`
- **断点提交**：
  ```bash
  git add src/agents/portfolio_agent.py tests/test_portfolio_agent.py
  git commit -m "feat(portfolio): add portfolio monitor agent"
  ```

### Step 5.4 推送通知（邮件/微信）

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：邮件发完整 HTML 表格，微信发摘要（可选）；单渠道失败不拖垮主流程（FR-PUSH-05）。
- **涉及文件**：`src/notifications/email_notifier.py`、`src/notifications/wechat_notifier.py`、`.env.example`（补 `SMTP_*`/`WECHAT_PUSH_ENABLED`，对齐 §10.2）
- **学习点**：**单渠道失败不拖垮整体**是稳定性护栏（NFR-04）。邮件挂了不能让整个分析流程崩。
- **验证**：配置 SMTP 后真实发一封测试邮件。
- **断点提交**：
  ```bash
  git add src/notifications/ tests/test_notifications.py
  git commit -m "feat(notify): add email and wechat push"
  ```

> 🎯 **M5 验收**：09:00/17:00 自动跑并推送（DoD 第 4 条）。每个断点提交后直接 `git push origin main`。

---

## M6 桌面端 UI

**目标**：Win/Mac 双端桌面应用可安装运行、可对话。
**验收**：Win/Mac 可安装运行。
**需求覆盖**：BR-13/15/16 · FR-UI-01~07 · NFR-01/02。

### Step 6.1 FastAPI 路由完善

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：补齐 dev-guide §11.1 剩余路由（`/chat` 已在 M4 完成）：`POST /pipeline/run`、`GET /report/{date}`、`POST /portfolio`、`GET /hotspot/{date}`、`GET /health`。
- **涉及文件**：`api/routes/*.py`
- **验证**：`uv run uvicorn api.app:app --reload`，逐个 curl 测。
- **断点提交**：
  ```bash
  git add api/routes/
  git commit -m "feat(api): complete fastapi routes"
  ```

### Step 6.2 Electron + React 骨架

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：在 `apps/desktop` 初始化 Electron + React + Vite，套壳本地 FastAPI；先做对话区与报告区。
- **涉及文件**：`apps/desktop/` 全部
- **学习点**：Electron = 用网页技术做桌面应用；它启动时拉起本地 FastAPI，前端通过 HTTP/SSE 调本地后端，数据不出本机（local-first）。
- **验证**：`cd apps/desktop && npm run dev` 能打开窗口并对话。
- **断点提交**：
  ```bash
  git add apps/desktop/
  git commit -m "feat(desktop): scaffold electron react app"
  ```

### Step 6.3 图标与完整仪表盘

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：制作巧克力色荷兰侏儒兔图标（`.ico`/`.icns`，C-08，FR-UI-02）；补持仓区、热点区、监控区；UI 明示"数据本地存储"（FR-UI-07）。
- **涉及文件**：`apps/desktop/assets/icon.*`、各页面组件
- **验证**：视觉评审图标风格；四个区都能显示数据。
- **断点提交**：
  ```bash
  git add apps/desktop/assets/ apps/desktop/src/
  git commit -m "feat(desktop): add icon and dashboard areas"
  ```

### Step 6.4 Win/Mac 打包

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：在 `manifests/` 配置 Win（nsis/portable）与 Mac（dmg）打包（FR-UI-06）。
- **涉及文件**：`manifests/win.yml`、`manifests/mac.yml`、`apps/desktop/electron-builder.*`
- **学习点**：平台差异收敛到打包配置，UI 代码共享一份（风险 R-07 缓解）。
- **验证**：分别打出 Win 与 Mac 安装包并安装运行。
- **断点提交**：
  ```bash
  git add manifests/ apps/desktop/electron-builder.yml
  git commit -m "build: add win mac packaging"
  ```

> 🎯 **M6 验收**：双端可安装运行、可对话（DoD 第 5、6 条）。每个断点提交后直接 `git push origin main`。

---

## M7 监控与反馈

**目标**：Agent 执行可观测，用户反馈可收集迭代。
**验收**：监控可查、反馈可写。
**需求覆盖**：BR-12（监控/反馈要素，§7.2）· NFR-05（可观测）。

### Step 7.1 Agent 执行链落盘与监控区

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：每次 Agent 执行记录 `agent_name / tools_called / tokens / latency / status / error`，落 `data/monitor/`；UI 监控区展示。
- **涉及文件**：`src/agents/trace.py`、`apps/desktop/src/monitor/`
- **验证**：跑一次流程后监控区能看到执行链。
- **断点提交**：
  ```bash
  git add src/agents/trace.py apps/desktop/src/monitor/
  git commit -m "feat(monitor): add agent execution trace"
  ```

### Step 7.2 用户反馈库

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：点赞/修正入 `data/feedback/`，用于 Prompt 与评分校准迭代（dev-guide §7.2 反馈要素）。
- **涉及文件**：`src/agents/feedback.py`、`api/routes/feedback.py`
- **验证**：UI 点赞后 `data/feedback/` 有记录。
- **断点提交**：
  ```bash
  git add src/agents/feedback.py api/routes/feedback.py
  git commit -m "feat(feedback): add user feedback store"
  ```

### Step 7.3 端到端验收与文档定稿

- [ ] 已完成此步（断点提交后打勾）

- **做什么**：按 dev-guide §12.3 DoD 逐项核对；定稿 `README.md` 与 `CHANGELOG.md`、`docs/architecture.md`。
- **涉及文件**：`README.md`、`CHANGELOG.md`、`docs/architecture.md`
- **验证**：跑一遍 DoD 清单全部打勾。
- **断点提交**：
  ```bash
  git add README.md CHANGELOG.md docs/architecture.md
  git commit -m "docs: finalize changelog readme and architecture"
  ```

> 🎯 **M7 验收**：DoD 全部打勾。每个断点提交后直接 `git push origin main`。

---

## 附：里程碑与提交总览

| 里程碑 | Step 数 | 提交数 | 需求覆盖（dev-guide §9） | 验收命令 | 推送方式 |
|---|---|---|---|---|---|
| M0 工程骨架 | 4 | 4 | 工程基线（支撑全部 FR/NFR） | `uv run pytest` | 直接推 main |
| M1 数据采集 | 4 | 4 | BR-01/02 · FR-DATA-01~10 · FR-UPDATE-02/03 | 5 股冒烟，xlsx 字段齐全 | 直接推 main |
| M2 评分评级 | 4 | 4 | BR-03/04/05 · FR-SCORE-01~09 · FR-RATE-01~04 | 阈值单测全覆盖；`-评分`/`-评级` xlsx | 直接推 main |
| M3 报告输出 | 3 | 3 | BR-06/07 · FR-REPORT-01~07 | step1~4 一键跑通 | 直接推 main |
| M4 Agent 编排 | 4 | 4 | BR-12/14/17 · AR-* · FR-CHAT-01~05 | 对话触发各 Agent | 直接推 main |
| M5 监控推送 | 4 | 4 | BR-08/09/10/11 · FR-HOTSPOT/PORT/PUSH · FR-UPDATE-01 | 09/17 定时 + 推送 | 直接推 main |
| M6 桌面端 | 4 | 4 | BR-13/15/16 · FR-UI-01~07 · NFR-01/02 | Win/Mac 可安装 | 直接推 main |
| M7 监控反馈 | 3 | 3 | BR-12（监控/反馈）· NFR-05 | DoD 全勾 | 直接推 main |

**合计**：30 个断点提交、8 个里程碑，全部直接推 main（不开分支、不开 PR），覆盖 dev-guide §9 全部 BR/FR。

---

## 附：断点学习小贴士

1. **每步只做一件事**：不要顺手改别的，保持 commit 干净，出问题好回滚（`git revert`）。
2. **提交前必验证**：`uv run ruff check . && uv run pytest -m "not network"` 是你的安全带。
3. **看不懂就停下来查**：每个 Step 的"学习点"是刻意写的，遇到陌生概念先搞懂再往下。
4. **用 `git log --oneline` 回顾**：定期看自己的提交历史，能直观看到成长轨迹。
5. **卡住了就回到上一个断点**：`git status` 看改动，`git checkout .` 丢弃未提交改动重试。
6. **提交说明按 dev-guide §12.2 写**：目的/摘要/验证/未验证项/风险/回滚——这是职业习惯，越早养成越好（不开 PR，所以写进 commit message）。
7. **对照需求覆盖**：每完成一个里程碑，回看本里程碑的「需求覆盖」行，确认对应 BR/FR 都已实现。
8. **断点即推送**：每完成一个 Step，`git commit` 后立即 `git push origin main`；main 永远保持可用基线，出问题用 `git revert` 回滚。

---

## 关联文档

- 总纲：[dev-guide.md](./dev-guide.md)（§9 功能需求清单 / §13 里程碑 / §12 验证门禁）
- 业务：[brd-1.md](./brd-1.md)
- 产品：[prd.md](./prd.md)
- 日志：[dev-log.md](./dev-log.md)
