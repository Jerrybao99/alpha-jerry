"""Tushare 接口注册表——所有 5000 积分可调用接口（优先 vip 高级接口）。

设计原则（owner 决策，对齐 brd-1.md §7.8 / dev-guide §8.1）：
- 财务三表 / 指标 / 预告 / 快报 / 主营构成优先使用 ``_vip`` 后缀接口
 （5000 积分，按报告期 ``period`` 批量取全市场，避免逐股调用）。
- 其余接口使用常规接口（≤5000 积分可调取，5000 积分频次更高或无总量限制）。
- 每个接口记录 ``api_name`` / ``vip_api_name`` / ``doc_url`` / ``min_points`` / ``description``。
- 业务代码通过本注册表获取接口名与文档链接，禁止硬编码（NFR-07）。

接口文档来源：https://tushare.pro/document/2
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TushareInterface:
    """Tushare 接口描述。

    Attributes:
        api_name: 常规接口名（2000 积分可调，按 ts_code 逐股取）。
        vip_api_name: vip 高级接口名（5000 积分，按 period 批量取全市场；无 vip 则同 api_name）。
        doc_url: 接口文档 URL。
        min_points: 最低积分要求。
        description: 接口中文描述。
    """

    api_name: str
    vip_api_name: str
    doc_url: str
    min_points: int
    description: str


_DOC = "https://tushare.pro/document/2?doc_id="

# ===== 5000 积分可调用接口注册表（优先 vip）=====
# key 为业务别名，与 REQUIREMENT_ALIGNMENT.endpoint 对齐。
TUSHARE_INTERFACES: dict[str, TushareInterface] = {
    "stock_basic": TushareInterface("stock_basic", "stock_basic", _DOC + "25", 2000, "股票列表（基础信息）"),
    "income": TushareInterface("income", "income_vip", _DOC + "33", 2000, "利润表（vip 按报告期取全市场）"),
    "balancesheet": TushareInterface(
        "balancesheet", "balancesheet_vip", _DOC + "36", 2000, "资产负债表（vip 按报告期取全市场）"
    ),
    "cashflow": TushareInterface("cashflow", "cashflow_vip", _DOC + "44", 2000, "现金流量表（vip 按报告期取全市场）"),
    "fina_indicator": TushareInterface(
        "fina_indicator", "fina_indicator_vip", _DOC + "79", 2000, "财务指标数据（vip 按报告期取全市场）"
    ),
    "daily_basic": TushareInterface("daily_basic", "daily_basic", _DOC + "32", 2000, "每日指标（5000 积分无总量限制）"),
    "fina_audit": TushareInterface("fina_audit", "fina_audit", _DOC + "80", 2000, "财务审计意见"),
    "dividend": TushareInterface("dividend", "dividend", _DOC + "103", 2000, "分红送股数据"),
    "pledge_stat": TushareInterface("pledge_stat", "pledge_stat", _DOC + "110", 2000, "股权质押统计数据"),
    "top10_holders": TushareInterface("top10_holders", "top10_holders", _DOC + "61", 2000, "前十大股东"),
    "top10_floatholders": TushareInterface(
        "top10_floatholders", "top10_floatholders", _DOC + "62", 2000, "前十大流通股东"
    ),
    "forecast": TushareInterface("forecast", "forecast_vip", _DOC + "45", 2000, "业绩预告（vip 按报告期取全市场）"),
    "express": TushareInterface("express", "express_vip", _DOC + "46", 2000, "业绩快报（vip 按报告期取全市场）"),
    "fina_mainbz": TushareInterface(
        "fina_mainbz", "fina_mainbz_vip", _DOC + "81", 2000, "主营业务构成（vip 按报告期取全市场）"
    ),
    "disclosure_date": TushareInterface("disclosure_date", "disclosure_date", _DOC + "162", 2000, "财报披露日期表"),
    "trade_cal": TushareInterface("trade_cal", "trade_cal", _DOC + "26", 2000, "交易日历"),
    "stk_holdernumber": TushareInterface("stk_holdernumber", "stk_holdernumber", _DOC + "166", 600, "股东人数"),
    "stk_holdertrade": TushareInterface("stk_holdertrade", "stk_holdertrade", _DOC + "175", 2000, "股东增减持"),
    "share_float": TushareInterface("share_float", "share_float", _DOC + "160", 120, "限售股解禁"),
    "repurchase": TushareInterface("repurchase", "repurchase", _DOC + "124", 2000, "股票回购"),
}


def get_vip_api_name(key: str) -> str:
    """获取接口的 vip 高级接口名（无 vip 则返回常规接口名）。"""
    return TUSHARE_INTERFACES[key].vip_api_name


def get_doc_url(key: str) -> str:
    """获取接口的文档 URL。"""
    return TUSHARE_INTERFACES[key].doc_url
