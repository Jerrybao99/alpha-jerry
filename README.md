# alpha-jerry

> A 股基本面分析的 AI Native 工具集——覆盖"数据采集 → 个股评分 → 个股评级 → 报告输出 → 持仓监控 → 热点追踪 → 推送通知"完整业务闭环，帮助个人投资者识别优质公司并持续监控持仓风险。

**状态**：设计阶段（M0 工程骨架进行中，详见 [ROADMAP](docs/ROADMAP.md)）。

## 定位

把机构级的基本面筛选逻辑，做成个人投资者桌面上随时可对话的智能助手。

- **本地优先**：数据本地存储，不上传云端，保护隐私。
- **对话驱动**：Win/Mac 双端桌面应用，自然语言即可触发全流程。
- **规则可审计**：评分/评级走纯函数 + 单测，一票否决可追溯。
- **非套壳 Agent**：多 Agent 编排 + RAG 知识库 + 路由 + 工具 + 记忆 + 监控 + 反馈。

## 技术栈

Python 3.12+ · DeepSeek V4 Pro · Tushare Pro · LangGraph · ChromaDB · FastAPI · Electron + React

## 文档

- [开发指南](docs/dev-guide.md)（单一事实来源）
- [路线图](docs/ROADMAP.md)（M0~M7 断点学习）
- [业务需求](docs/brd-1.md) · [产品需求](docs/prd.md) · [开发日志](docs/dev-log.md)

## 快速开始

> 代码尚未落地，当前仅有设计文档。按 [ROADMAP](docs/ROADMAP.md) M0 起逐步实现。

```bash
# 安装依赖（M0 Step 0.2 后可用）
uv sync

# 配置密钥
cp .env.example .env   # 填入 DEEPSEEK_API_KEY / TUSHARE_TOKEN

# 运行测试
uv run pytest
```

## 免责声明

本项目输出仅供参考，不构成投资建议。投资决策由用户自行完成并自担风险。
