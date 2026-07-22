"""字段标准化输出辅助（§8.1）。

- 百分比字段（PERCENT_FIELDS）加 ``%`` 后缀保留两位小数。
- 其余字段保持原始值（None 归一化为 None；大数的科学计数法显示由 xlsx_writer 写盘时处理）。
- ``to_output_row``：按 ALL_OUTPUT_COLUMNS 顺序提取，供写盘列对齐。

纯函数，便于单测。
"""

from __future__ import annotations

from typing import Any

from src.schemas.financial import ALL_OUTPUT_COLUMNS, PERCENT_FIELDS, StockFeatures


def format_percent(value: float | None) -> str | None:
    """百分比格式化：30.5 → ``30.50%``；None → None。"""
    if value is None:
        return None
    return f"{value:.2f}%"


def to_output_row(features: StockFeatures) -> dict[str, Any]:
    """按 ALL_OUTPUT_COLUMNS 顺序提取字段；百分比字段格式化为字符串，其余原值。

    保证写盘列与 §8.1 字段契约一致，不缺列、不多列。
    """
    dumped = features.model_dump()
    row: dict[str, Any] = {}
    for col in ALL_OUTPUT_COLUMNS:
        value = dumped.get(col)
        row[col] = format_percent(value) if col in PERCENT_FIELDS else value
    return row
