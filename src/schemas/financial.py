"""特征工程字段模型——以 Tushare 真实字段为输出列（对齐官方文档）。

设计原则（依项目 owner 决策）：
- 采集落地的 CSV/列全部使用 Tushare 接口真实返回字段名与真实数据，不自造中文字段名、不存计算字段。
- §8.1 的 55 个"需求字段"作为采购清单，逐一对齐到 Tushare 真实字段：
  exact 精确对应 / approximate 近似替代 / computed_in_scoring 评分时由真实字段计算 /
  unavailable Tushare 无此字段且无近似，首版不采集。
- 计算型需求字段（主营利润率、股东权益比等）不在采集文件中存储，留给 M2 评分纯函数计算，
  保证采集层只有"真实字段 + 真实数据"，评分层只做纯逻辑（dev-guide §6.3 原则 4）。

字段来源对齐：https://tushare.pro/document/2
  stock_basic / income / balancesheet / cashflow / fina_indicator / daily_basic
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

# ===== Tushare 接口常量 =====
STOCK_BASIC = "stock_basic"
INCOME = "income"
BALANCESHEET = "balancesheet"
CASHFLOW = "cashflow"
FINA_INDICATOR = "fina_indicator"
DAILY_BASIC = "daily_basic"
COMPUTED = "computed_in_scoring"  # 评分时由真实字段计算，不落盘
UNAVAILABLE = "unavailable"  # Tushare 无此字段且无近似，首版不采集


@dataclass(frozen=True)
class RequirementAlign:
    """§8.1 需求字段 → Tushare 真实字段的对齐记录。"""

    requirement: str  # §8.1 中文名
    endpoint: str  # 来源接口（或 COMPUTED / UNAVAILABLE）
    tushare_field: str | tuple[str, ...] | None  # 对应 Tushare 真实字段名
    match: str  # exact / approximate / computed_in_scoring / unavailable
    note: str = ""


# ===== §8.1 需求字段（55）→ Tushare 真实字段对齐表 =====
REQUIREMENT_ALIGNMENT: list[RequirementAlign] = [
    RequirementAlign("股票代码", STOCK_BASIC, "symbol", "exact"),
    RequirementAlign("股票名称", STOCK_BASIC, "name", "exact"),
    RequirementAlign("行业属性", STOCK_BASIC, "industry", "exact"),
    RequirementAlign("上市日期", STOCK_BASIC, "list_date", "exact"),
    RequirementAlign("财报发布日期", INCOME, "ann_date", "exact", "公告日期"),
    RequirementAlign("财报所属期间", INCOME, "end_date", "exact", "报告期如 20171231"),
    RequirementAlign("主营收入", INCOME, "revenue", "approximate", "营业收入近似主营收入"),
    RequirementAlign("主营利润", INCOME, "operate_profit", "approximate", "无主营利润字段，以营业利润近似"),
    RequirementAlign("营业利润", INCOME, "operate_profit", "exact"),
    RequirementAlign("投资收益", INCOME, "invest_income", "exact", "投资净收益"),
    RequirementAlign(
        "营业外收支", INCOME, ("non_oper_income", "non_oper_exp"), "approximate", "拆为营业外收入/支出两列真实字段"
    ),
    RequirementAlign("利润总额", INCOME, "total_profit", "exact"),
    RequirementAlign("净利润", INCOME, "n_income_attr_p", "exact", "归属母公司股东净利润"),
    RequirementAlign("未分配利润", BALANCESHEET, "undistr_porfit", "exact", "Tushare 字段名本身拼写为 porfit"),
    RequirementAlign("总资产", BALANCESHEET, "total_assets", "exact"),
    RequirementAlign("流动资产", BALANCESHEET, "total_cur_assets", "exact", "流动资产合计"),
    RequirementAlign("固定资产", BALANCESHEET, "fix_assets", "exact"),
    RequirementAlign("无形资产", BALANCESHEET, "intan_assets", "exact"),
    RequirementAlign("总负债", BALANCESHEET, "total_liab", "exact", "负债合计"),
    RequirementAlign("流动负债", BALANCESHEET, "total_cur_liab", "exact", "流动负债合计"),
    RequirementAlign("长期负债", BALANCESHEET, "total_ncl", "exact", "非流动负债合计"),
    RequirementAlign("股东权益", BALANCESHEET, "total_hldr_eqy_exc_min_int", "exact", "不含少数股东权益"),
    RequirementAlign("资本公积金", BALANCESHEET, "cap_rese", "exact"),
    RequirementAlign("经营现金流量", CASHFLOW, "n_cashflow_act", "exact", "经营活动现金流量净额"),
    RequirementAlign("投资现金流量", CASHFLOW, "n_cashflow_inv_act", "exact"),
    RequirementAlign("筹资现金流量", CASHFLOW, "n_cash_flows_fnc_act", "exact"),
    RequirementAlign("现金增加额", CASHFLOW, "n_incr_cash_cash_equ", "exact", "现金及现金等价物净增加额"),
    RequirementAlign("每股收益", FINA_INDICATOR, "eps", "exact"),
    RequirementAlign("每股净资产", FINA_INDICATOR, "bps", "exact"),
    RequirementAlign("净资产收益率", FINA_INDICATOR, "roe", "exact"),
    RequirementAlign("每股经营现金", FINA_INDICATOR, "ocfps", "exact"),
    RequirementAlign("每股公积金", FINA_INDICATOR, "capital_rese_ps", "exact", "每股资本公积"),
    RequirementAlign("每股未分配利润", FINA_INDICATOR, "undist_profit_ps", "exact"),
    RequirementAlign(
        "股东权益比", COMPUTED, None, "computed_in_scoring", "= total_hldr_eqy_exc_min_int / total_assets"
    ),
    RequirementAlign("净利润同比增长率", FINA_INDICATOR, "netprofit_yoy", "exact", "归母净利润同比(%)"),
    RequirementAlign("主营收入同比增长率", FINA_INDICATOR, "or_yoy", "exact", "营业收入同比(%)"),
    RequirementAlign("销售毛利率", FINA_INDICATOR, "grossprofit_margin", "exact"),
    RequirementAlign("调整后每股净资产", UNAVAILABLE, None, "unavailable", "Tushare 无此字段且无近似，首版不采集"),
    RequirementAlign("总股本", BALANCESHEET, "total_share", "exact", "期末总股本"),
    RequirementAlign("无限售股合计", DAILY_BASIC, "float_share", "approximate", "流通股本近似无限售股合计"),
    RequirementAlign("A股数量", UNAVAILABLE, None, "unavailable", "Tushare 无此字段，首版不采集"),
    RequirementAlign("B股数量", UNAVAILABLE, None, "unavailable", "Tushare 无此字段，首版不采集"),
    RequirementAlign("限售股合计", COMPUTED, None, "computed_in_scoring", "= total_share - float_share"),
    RequirementAlign("国家持股数量", UNAVAILABLE, None, "unavailable", "需 top10_holders 聚合，首版不采集"),
    RequirementAlign("国有法人持股", UNAVAILABLE, None, "unavailable", "需 top10_holders 聚合，首版不采集"),
    RequirementAlign("资产负债率", FINA_INDICATOR, "debt_to_assets", "exact", "(%)"),
    RequirementAlign("流动比率", FINA_INDICATOR, "current_ratio", "exact"),
    RequirementAlign("速动比率", FINA_INDICATOR, "quick_ratio", "exact"),
    RequirementAlign("权益乘数", FINA_INDICATOR, "assets_to_eqt", "exact"),
    RequirementAlign("每股经营现金流/每股收益", COMPUTED, None, "computed_in_scoring", "= ocfps / eps"),
    RequirementAlign("净利润占营业利润比", COMPUTED, None, "computed_in_scoring", "= n_income_attr_p / operate_profit"),
    RequirementAlign("主营利润率", COMPUTED, None, "computed_in_scoring", "需先算主营利润，再 / revenue"),
    RequirementAlign("净利率", FINA_INDICATOR, "netprofit_margin", "exact", "销售净利率(%)"),
    RequirementAlign("投资收益占比", COMPUTED, None, "computed_in_scoring", "= invest_income / total_profit"),
    RequirementAlign("现金流量比率", FINA_INDICATOR, "ocf_to_shortdebt", "exact", "经营现金流/流动负债"),
]

# ===== 各接口需请求的真实字段（供 TushareFetcher 拼 fields= 参数）=====
STOCK_BASIC_FIELDS: tuple[str, ...] = ("ts_code", "symbol", "name", "industry", "list_date")
INCOME_FIELDS: tuple[str, ...] = (
    "ts_code",
    "ann_date",
    "end_date",
    "revenue",
    "operate_profit",
    "invest_income",
    "non_oper_income",
    "non_oper_exp",
    "total_profit",
    "n_income_attr_p",
)
BALANCESHEET_FIELDS: tuple[str, ...] = (
    "ts_code",
    "undistr_porfit",
    "total_assets",
    "total_cur_assets",
    "fix_assets",
    "intan_assets",
    "total_liab",
    "total_cur_liab",
    "total_ncl",
    "total_hldr_eqy_exc_min_int",
    "cap_rese",
    "total_share",
)
CASHFLOW_FIELDS: tuple[str, ...] = (
    "ts_code",
    "n_cashflow_act",
    "n_cashflow_inv_act",
    "n_cash_flows_fnc_act",
    "n_incr_cash_cash_equ",
)
FINA_INDICATOR_FIELDS: tuple[str, ...] = (
    "ts_code",
    "eps",
    "bps",
    "roe",
    "ocfps",
    "capital_rese_ps",
    "undist_profit_ps",
    "netprofit_yoy",
    "or_yoy",
    "grossprofit_margin",
    "debt_to_assets",
    "current_ratio",
    "quick_ratio",
    "assets_to_eqt",
    "netprofit_margin",
    "ocf_to_shortdebt",
)
DAILY_BASIC_FIELDS: tuple[str, ...] = ("ts_code", "trade_date", "float_share")

# 输出列顺序（Tushare 真实字段名）；ts_code 为主键置首。
OUTPUT_COLUMNS: tuple[str, ...] = (
    *STOCK_BASIC_FIELDS,
    *INCOME_FIELDS[1:],  # 去重 ts_code
    *BALANCESHEET_FIELDS[1:],
    *CASHFLOW_FIELDS[1:],
    *FINA_INDICATOR_FIELDS[1:],
    *DAILY_BASIC_FIELDS[1:],
)

# Tushare 以百分数数值返回的字段（如 30.5 表示 30.5%）；写盘时按 dev-log 加 % 后缀。
PERCENT_FIELDS: frozenset[str] = frozenset(
    {
        "netprofit_yoy",
        "or_yoy",
        "grossprofit_margin",
        "debt_to_assets",
        "netprofit_margin",
    }
)


class StockInfo(BaseModel):
    """上市公司清单条目（来源 stock_basic，字段名即 Tushare 真实字段名）。"""

    model_config = ConfigDict(populate_by_name=True)

    ts_code: str
    symbol: str = ""
    name: str = ""
    industry: str = ""
    list_date: str | None = None


class StockFeatures(BaseModel):
    """单股特征工程数据——字段名即 Tushare 真实返回字段名，数据为真实值。

    采集层只存真实字段；§8.1 中的计算型需求（股东权益比/主营利润率等）
    不在此模型，由 M2 评分纯函数基于这些真实字段计算。
    """

    model_config = ConfigDict(populate_by_name=True)

    # —— stock_basic ——
    ts_code: str
    symbol: str = ""
    name: str = ""
    industry: str = ""
    list_date: str | None = None
    # —— income ——
    ann_date: str | None = None
    end_date: str | None = None
    revenue: float | None = None
    operate_profit: float | None = None
    invest_income: float | None = None
    non_oper_income: float | None = None
    non_oper_exp: float | None = None
    total_profit: float | None = None
    n_income_attr_p: float | None = None
    # —— balancesheet ——
    undistr_porfit: float | None = None
    total_assets: float | None = None
    total_cur_assets: float | None = None
    fix_assets: float | None = None
    intan_assets: float | None = None
    total_liab: float | None = None
    total_cur_liab: float | None = None
    total_ncl: float | None = None
    total_hldr_eqy_exc_min_int: float | None = None
    cap_rese: float | None = None
    total_share: float | None = None
    # —— cashflow ——
    n_cashflow_act: float | None = None
    n_cashflow_inv_act: float | None = None
    n_cash_flows_fnc_act: float | None = None
    n_incr_cash_cash_equ: float | None = None
    # —— fina_indicator ——
    eps: float | None = None
    bps: float | None = None
    roe: float | None = None
    ocfps: float | None = None
    capital_rese_ps: float | None = None
    undist_profit_ps: float | None = None
    netprofit_yoy: float | None = None
    or_yoy: float | None = None
    grossprofit_margin: float | None = None
    debt_to_assets: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    assets_to_eqt: float | None = None
    netprofit_margin: float | None = None
    ocf_to_shortdebt: float | None = None
    # —— daily_basic ——
    trade_date: str | None = None
    float_share: float | None = None

    @classmethod
    def output_columns(cls) -> list[str]:
        """输出 CSV/表的列名（Tushare 真实字段名，按 OUTPUT_COLUMNS 顺序）。"""
        return list(OUTPUT_COLUMNS)


def requirement_coverage() -> dict[str, int]:
    """统计 §8.1 需求字段的对齐覆盖情况，供文档/报告使用。"""
    counts: dict[str, int] = {}
    for a in REQUIREMENT_ALIGNMENT:
        counts[a.match] = counts.get(a.match, 0) + 1
    return counts
