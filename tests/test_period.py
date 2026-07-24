"""expected_latest_period 纯函数单测，对齐各披露截止日边界。"""

from __future__ import annotations

import datetime as _dt

from src.utils.period import expected_latest_period


def test_mid_year_after_q1_deadline() -> None:
    """7 月：一季报已披露，半年报未到截止日 → 20260331。"""
    assert expected_latest_period(_dt.date(2026, 7, 24)) == "20260331"


def test_q1_deadline_day() -> None:
    """4-30 当天：一季报与上年年报均到截止日，取较大者 20260331。"""
    assert expected_latest_period(_dt.date(2026, 4, 30)) == "20260331"


def test_day_before_q1_deadline() -> None:
    """4-29：一季报与上年年报均未到截止日 → 退到去年 Q3 20250930。"""
    assert expected_latest_period(_dt.date(2026, 4, 29)) == "20250930"


def test_after_q1_before_semi() -> None:
    """5 月：一季报已披露、半年报未到 → 20260331。"""
    assert expected_latest_period(_dt.date(2026, 5, 15)) == "20260331"


def test_semi_deadline_day() -> None:
    """8-31 当天：半年报到截止日 → 20260630。"""
    assert expected_latest_period(_dt.date(2026, 8, 31)) == "20260630"


def test_before_q3_deadline() -> None:
    """9 月中：三季报未到截止日 → 20260630。"""
    assert expected_latest_period(_dt.date(2026, 9, 15)) == "20260630"


def test_q3_deadline_day() -> None:
    """10-31 当天：三季报到截止日 → 20260930。"""
    assert expected_latest_period(_dt.date(2026, 10, 31)) == "20260930"


def test_year_end_before_annual() -> None:
    """12-31：本年年报未到截止日(次年4-30) → 20260930。"""
    assert expected_latest_period(_dt.date(2026, 12, 31)) == "20260930"


def test_january_before_q1() -> None:
    """1 月：本年一季报/上年年报均未到截止日 → 上年 Q3 20250930。"""
    assert expected_latest_period(_dt.date(2026, 1, 15)) == "20250930"


def test_returns_string_yyyymmdd() -> None:
    """返回值为 8 位 YYYYMMDD 字符串。"""
    s = expected_latest_period(_dt.date(2026, 7, 24))
    assert isinstance(s, str)
    assert len(s) == 8
    assert s.isdigit()
