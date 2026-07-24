"""按法定披露截止日推算「最新应已披露报告期」。纯函数，便于单测对齐边界。

A股法定披露截止日：Q1(0331)→4-30、半年报(0630)→8-31、Q3(0930)→10-31、年报(1231)→次年4-30。
给定今天，返回最近一个披露截止日 ≤ 今天的报告期（YYYYMMDD）。
用于校验采集到的 end_date 是否陈旧（应 ≥ 该值）。
"""

from __future__ import annotations

import datetime as _dt

# 报告期月日 → 披露截止日（按报告期年份计算）
_DEADLINES: dict[str, _dt.date] = {
    "0331": _dt.date(2026, 4, 30),  # Q1：同年 4-30（年份在 _deadline 里替换）
    "0630": _dt.date(2026, 8, 31),  # 半年报：同年 8-31
    "0930": _dt.date(2026, 10, 31),  # Q3：同年 10-31
    "1231": _dt.date(2027, 4, 30),  # 年报：次年 4-30
}


def _deadline(period: str) -> _dt.date:
    """报告期(YYYYMMDD) → 法定披露截止日。"""
    y = int(period[:4])
    md = period[4:]
    base = _DEADLINES[md]
    if md == "1231":
        return base.replace(year=y + 1)
    return base.replace(year=y)


def expected_latest_period(today: _dt.date) -> str:
    """返回今天理应已披露的最新报告期（YYYYMMDD）。

    遍历今年与去年四个报告期，取披露截止日 ≤ today 的最大者。
    """
    candidates: list[str] = []
    for y in (today.year, today.year - 1):
        for md in _DEADLINES:
            p = f"{y}{md}"
            if _deadline(p) <= today:
                candidates.append(p)
    # today 至少晚于去年 Q3 的披露截止日(去年10-31)，candidates 必非空
    return max(candidates) if candidates else f"{today.year - 1}0930"
