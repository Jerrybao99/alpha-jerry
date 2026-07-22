"""CSV 落地写入器。写两张 CSV：YYMMDD.csv（中文列头+百分比带%+大数亿/万+CJK 对齐）与
YYMMDD-数据来源.csv（接口/字段/中文/URL）。字段中文名映射取自 REQUIREMENT_ALIGNMENT + SUPPLEMENTARY_FIELDS。
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from src.data.interfaces import TUSHARE_INTERFACES, get_vip_api_name
from src.schemas.financial import (
    ALL_OUTPUT_COLUMNS,
    BALANCESHEET_FIELDS,
    CASHFLOW_FIELDS,
    DAILY_BASIC_FIELDS,
    DIVIDEND_FIELDS,
    FINA_AUDIT_FIELDS,
    FINA_INDICATOR_FIELDS,
    INCOME_FIELDS,
    PERCENT_FIELDS,
    PLEDGE_STAT_FIELDS,
    REQUIREMENT_ALIGNMENT,
    STOCK_BASIC_FIELDS,
    SUPPLEMENTARY_FIELDS,
    StockFeatures,
)

# 字段 → 中文显示名（先从需求对齐表/补充字段构造，再补缺口）
FIELD_CN: dict[str, str] = {}
for _a in REQUIREMENT_ALIGNMENT:
    if isinstance(_a.tushare_field, str):
        FIELD_CN[_a.tushare_field] = _a.chinese_name
    elif isinstance(_a.tushare_field, tuple):
        for _f in _a.tushare_field:
            FIELD_CN[_f] = _a.chinese_name
for _sf in SUPPLEMENTARY_FIELDS:
    FIELD_CN[_sf.tushare_field] = _sf.chinese_name
# REQUIREMENT_ALIGNMENT 未覆盖的列
FIELD_CN.update(
    {
        "ts_code": "股票代码(ts_code)",
        "trade_date": "交易日",
        "div_proc": "分红进度",
        "non_oper_income": "营业外收入",
        "non_oper_exp": "营业外支出",
    }
)

# 字段 → 来源接口别名（取自各接口字段集，便于生成数据来源表）
_FIELD_TO_INTERFACE: dict[str, str] = {}
for _iface, _fields in (
    ("stock_basic", STOCK_BASIC_FIELDS),
    ("income", INCOME_FIELDS),
    ("balancesheet", BALANCESHEET_FIELDS),
    ("cashflow", CASHFLOW_FIELDS),
    ("fina_indicator", FINA_INDICATOR_FIELDS),
    ("daily_basic", DAILY_BASIC_FIELDS),
    ("fina_audit", FINA_AUDIT_FIELDS),
    ("pledge_stat", PLEDGE_STAT_FIELDS),
    ("dividend", DIVIDEND_FIELDS),
):
    for _f in _fields:
        _FIELD_TO_INTERFACE[_f] = _iface


def display_width(s: str) -> int:
    """CJK 感知的显示宽度：宽字符(W/F/A)计 2，其余计 1。"""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F", "A") else 1 for c in s)


def format_value(field: str, value: Any) -> str:
    """按 §8.1 格式化单元格：百分比加 % 两位小数；大数用亿/万；None→空串。"""
    if value is None:
        return ""
    if field in PERCENT_FIELDS:
        return f"{float(value):.2f}%"
    if isinstance(value, (int, float)):
        v = float(value)
        if abs(v) >= 1e8:
            return f"{v / 1e8:.2f}亿"
        if abs(v) >= 1e4:
            return f"{v / 1e4:.2f}万"
        return f"{v:.2f}"
    return str(value)


def _pad(cell: str, width: int) -> str:
    """按显示宽度右补空格对齐到 width。"""
    return cell + " " * (width - display_width(cell))


def write_features_csv(features: list[StockFeatures], out_path: Path) -> Path:
    """写特征数据 CSV：中文列头 + 格式化值 + CJK 对齐。"""
    headers = [FIELD_CN[c] for c in ALL_OUTPUT_COLUMNS]
    rows: list[list[str]] = []
    for feat in features:
        dumped = feat.model_dump()
        rows.append([format_value(c, dumped.get(c)) for c in ALL_OUTPUT_COLUMNS])

    # 每列宽度 = max(列头显示宽, 各值显示宽)
    col_widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], display_width(cell))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = len(ALL_OUTPUT_COLUMNS)

    def build(cells: list[str]) -> str:
        # 最后一列不填充，避免每行尾随空格；其余列按显示宽度右补空格对齐
        parts = [_pad(c, col_widths[i]) if i < n - 1 else c for i, c in enumerate(cells)]
        return ",".join(parts)

    lines: list[str] = []
    lines.append(build(headers))
    for row in rows:
        lines.append(build(row))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return out_path


def write_data_source_csv(out_path: Path) -> Path:
    """写数据来源 CSV：接口/字段/字段中文/文档URL（仅采集器实际采用的接口与字段）。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["接口,字段,字段中文,文档URL"]
    for field in ALL_OUTPUT_COLUMNS:
        iface_key = _FIELD_TO_INTERFACE.get(field)
        if iface_key is None:
            continue
        iface = TUSHARE_INTERFACES[iface_key]
        api_name = get_vip_api_name(iface_key)
        cn = FIELD_CN.get(field, field)
        lines.append(f"{api_name},{field},{cn},{iface.doc_url}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return out_path
