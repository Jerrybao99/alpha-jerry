---
tags: [data-contract, 字段契约, single-source-of-truth]
status: active
version: 1.0.0
date: 2026-07-23
关联文档: [brd-1.md](./brd-1.md) §7.8, [dev-guide.md](./dev-guide.md) §8.1, [ROADMAP.md](./ROADMAP.md) Step 1.1
---

# alpha-jerry 字段契约文档（data-contract）

> 本文件是采集层字段契约的详细说明，补充 dev-guide §8.1 的字段对齐表。
> 单一事实来源为代码：`src/schemas/financial.py`（`REQUIREMENT_ALIGNMENT` + `SUPPLEMENTARY_FIELDS`）
> 与 `src/data/interfaces.py`（`TUSHARE_INTERFACES`）。
> 字段对应表 CSV：`docs/field-mapping.csv`（可用 `uv run python scripts/gen_field_mapping.py` 重新生成）。

---

## 1. 采集策略

### 1.1 接口选型原则

- **优先 vip 高级接口**：财务三表 / 指标 / 预告 / 快报 / 主营构成使用 `_vip` 后缀接口（5000 积分，按 `period` 批量取全市场），避免逐股调用。
- **5000 积分可调用**：所有接口均可在 5000 积分下调用（常规接口 2000 积分起，vip 接口 5000 积分）。
- **接口注册表**：`src/data/interfaces.py` 的 `TUSHARE_INTERFACES` 记录每个接口的 `api_name` / `vip_api_name` / `doc_url` / `min_points` / `description`。

### 1.2 接口清单（20 个，5000 积分可调用）

| 业务别名 | 常规接口 | vip 接口 | 最低积分 | 文档 URL | 用途 |
|---|---|---|---|---|---|
| stock_basic | stock_basic | — | 2000 | [doc_id=25](https://tushare.pro/document/2?doc_id=25) | 股票列表 |
| income | income | **income_vip** | 2000 | [doc_id=33](https://tushare.pro/document/2?doc_id=33) | 利润表 |
| balancesheet | balancesheet | **balancesheet_vip** | 2000 | [doc_id=36](https://tushare.pro/document/2?doc_id=36) | 资产负债表 |
| cashflow | cashflow | **cashflow_vip** | 2000 | [doc_id=44](https://tushare.pro/document/2?doc_id=44) | 现金流量表 |
| fina_indicator | fina_indicator | **fina_indicator_vip** | 2000 | [doc_id=79](https://tushare.pro/document/2?doc_id=79) | 财务指标 |
| daily_basic | daily_basic | — | 2000 | [doc_id=32](https://tushare.pro/document/2?doc_id=32) | 每日指标 |
| fina_audit | fina_audit | — | 2000 | [doc_id=80](https://tushare.pro/document/2?doc_id=80) | 财务审计意见 |
| dividend | dividend | — | 2000 | [doc_id=103](https://tushare.pro/document/2?doc_id=103) | 分红送股 |
| pledge_stat | pledge_stat | — | 2000 | [doc_id=110](https://tushare.pro/document/2?doc_id=110) | 股权质押统计 |
| top10_holders | top10_holders | — | 2000 | [doc_id=61](https://tushare.pro/document/2?doc_id=61) | 前十大股东 |
| top10_floatholders | top10_floatholders | — | 2000 | [doc_id=62](https://tushare.pro/document/2?doc_id=62) | 前十大流通股东 |
| forecast | forecast | **forecast_vip** | 2000 | [doc_id=45](https://tushare.pro/document/2?doc_id=45) | 业绩预告 |
| express | express | **express_vip** | 2000 | [doc_id=46](https://tushare.pro/document/2?doc_id=46) | 业绩快报 |
| fina_mainbz | fina_mainbz | **fina_mainbz_vip** | 2000 | [doc_id=81](https://tushare.pro/document/2?doc_id=81) | 主营业务构成 |
| disclosure_date | disclosure_date | — | 2000 | [doc_id=162](https://tushare.pro/document/2?doc_id=162) | 财报披露日期 |
| trade_cal | trade_cal | — | 2000 | [doc_id=26](https://tushare.pro/document/2?doc_id=26) | 交易日历 |
| stk_holdernumber | stk_holdernumber | — | 600 | [doc_id=166](https://tushare.pro/document/2?doc_id=166) | 股东人数 |
| stk_holdertrade | stk_holdertrade | — | 2000 | [doc_id=175](https://tushare.pro/document/2?doc_id=175) | 股东增减持 |
| share_float | share_float | — | 120 | [doc_id=160](https://tushare.pro/document/2?doc_id=160) | 限售股解禁 |
| repurchase | repurchase | — | 2000 | [doc_id=124](https://tushare.pro/document/2?doc_id=124) | 股票回购 |

> vip 接口优势：按 `period`（报告期）一次取全市场所有股票，无需逐股调用，大幅减少 API 请求次数与积分消耗。

---

## 2. 字段对齐总览

### 2.1 brd-1.md §7.8 的 55 个需求字段

| 对齐类型 | 数量 | 含义 |
|---|---|---|
| exact | 40 | Tushare 有精确字段，直接采集 |
| approximate | 4 | 无精确字段取最近似替代 |
| computed_in_scoring | 6 | 不落盘，由 M2 评分纯函数基于真实字段计算 |
| unavailable | 5 | Tushare 无且无近似，首版不采集 |

### 2.2 补充字段（13 个，服务一票否决 §8.2 / 三维评分 §8.3）

| 用途 | 字段 | 来源接口 |
|---|---|---|
| veto（造假嫌疑） | money_cap（货币资金）, fin_exp_int_inc（财务费用利息收入） | balancesheet_vip / income_vip |
| veto（诚信问题） | audit_result（审计结果）, audit_agency（会计事务所）, pledge_ratio（质押比例） | fina_audit / pledge_stat |
| scoring（资金回报） | free_cashflow（自由现金流）, pe_ttm（市盈率TTM）, pb（市净率）, dv_ttm（股息率TTM）, cash_div（每股分红）, total_mv（总市值）, circ_mv（流通市值） | cashflow_vip / daily_basic / dividend |
| scoring（稳健性） | inv_turn（存货周转率） | fina_indicator_vip |

---

## 3. 计算型字段口径

以下 6 个需求字段不在采集层存储，由 M2 评分纯函数基于真实字段计算：

| 需求字段 | 计算公式 | 依赖真实字段 |
|---|---|---|
| 股东权益比 | `total_hldr_eqy_exc_min_int / total_assets` | balancesheet_vip |
| 限售股合计 | `total_share - float_share` | balancesheet_vip + daily_basic |
| 每股经营现金流/每股收益 | `ocfps / eps` | fina_indicator_vip |
| 净利润占营业利润比 | `n_income_attr_p / operate_profit` | income_vip |
| 主营利润率 | `operate_profit / revenue` | income_vip |
| 投资收益占比 | `invest_income / total_profit` | income_vip |

---

## 4. 百分比字段

以下字段 Tushare 以百分数数值返回（如 30.5 表示 30.5%），写盘时加 `%` 后缀保留两位小数：

`netprofit_yoy`, `or_yoy`, `grossprofit_margin`, `debt_to_assets`, `netprofit_margin`, `dv_ttm`

---

## 5. 不可用字段（5 个）

| 需求字段 | 原因 |
|---|---|
| 调整后每股净资产 | Tushare 无此字段且无近似 |
| A股数量 | Tushare 无此字段 |
| B股数量 | Tushare 无此字段 |
| 国家持股数量 | 需 top10_holders 聚合，首版不采集 |
| 国有法人持股 | 需 top10_holders 聚合，首版不采集 |

---

## 6. 字段对应表 CSV

完整字段对应表见 `docs/field-mapping.csv`（UTF-8 BOM 编码，Excel 可直接打开）。

列说明：

| 列名 | 说明 |
|---|---|
| 序号 | 1–68 |
| BRD需求字段 | brd-1.md §7.8 需求字段中文名（补充字段标记"（补充）"） |
| Tushare真实字段名 | Tushare 接口真实返回字段名 |
| 字段中文翻译 | 真实字段的中文翻译 |
| 来源接口(vip优先) | 使用的接口名（vip 优先） |
| 接口文档URL | Tushare 官方文档链接 |
| 积分要求 | 接口最低积分要求 |
| 对齐类型 | exact / approximate / computed_in_scoring / unavailable / supplementary |
| 用途 | 特征工程 / veto / scoring |
| 备注 | 补充说明 |

重新生成：`uv run python scripts/gen_field_mapping.py`

---

## 7. 关联文档

- 业务需求：[brd-1.md](./brd-1.md) §7.8
- 开发指南：[dev-guide.md](./dev-guide.md) §8.1
- 路线图：[ROADMAP.md](./ROADMAP.md) Step 1.1 / 1.2
- 代码：`src/schemas/financial.py` / `src/data/interfaces.py`
- 生成脚本：`scripts/gen_field_mapping.py`
