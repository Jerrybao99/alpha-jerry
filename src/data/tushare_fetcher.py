"""Tushare 数据源适配器。实现 BaseFetcher，含限流器（每分钟调用上限）与指数退避重试（1s/2s/4s）。
财务四表等优先用 _vip 接口；token 从 Settings 读取注入 SDK，空则报错提示配置 .env。
"""

from __future__ import annotations

import math
import time
from collections import deque
from collections.abc import Callable
from typing import Any

import tushare as ts

from src.config import Settings, get_settings
from src.data.base import BaseFetcher
from src.data.interfaces import get_vip_api_name
from src.schemas.financial import (
    BALANCESHEET_FIELDS,
    CASHFLOW_FIELDS,
    DAILY_BASIC_FIELDS,
    DIVIDEND_FIELDS,
    FINA_AUDIT_FIELDS,
    FINA_INDICATOR_FIELDS,
    INCOME_FIELDS,
    PLEDGE_STAT_FIELDS,
    STOCK_BASIC_FIELDS,
    StockFeatures,
    StockInfo,
)

# 指数退避基数（秒）：1, 2, 4
BACKOFF_BASE_SECONDS = 1.0
DEFAULT_MAX_RETRIES = 3
RATE_WINDOW_SECONDS = 60.0


class TushareTokenError(RuntimeError):
    """TUSHARE_TOKEN 缺失或无效。"""


class TushareApiError(RuntimeError):
    """Tushare 接口调用失败（重试耗尽）。"""


class RateLimiter:
    """滑动窗口限流器：每 ``window`` 秒最多 ``limit`` 次调用，超额则阻塞到窗口腾位。

    clock/sleep 可注入，便于单测（FR-DATA-06）。
    """

    def __init__(
        self,
        limit: int,
        *,
        window: float = RATE_WINDOW_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = max(1, limit)
        self.window = window
        self._sleep = sleep
        self._clock = clock
        self._stamps: deque[float] = deque()

    def acquire(self) -> None:
        """获取一个调用名额，必要时 sleep 等待。"""
        now = self._clock()
        self._evict(now)
        if len(self._stamps) >= self.limit:
            wait = self.window - (now - self._stamps[0])
            if wait > 0:
                self._sleep(wait)
                now = self._clock()  # sleep 后重新取时间
                self._evict(now)
        self._stamps.append(now)

    def _evict(self, now: float) -> None:
        while self._stamps and now - self._stamps[0] >= self.window:
            self._stamps.popleft()


class TushareFetcher(BaseFetcher):
    """Tushare 适配器：限流 + 指数退避重试 + vip 接口优先。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        pro: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.settings = settings or get_settings()
        self._max_retries = max(0, max_retries)
        self._sleep = sleep
        self._clock = clock
        self._limiter = RateLimiter(self.settings.tushare_rate_limit, sleep=sleep, clock=clock)
        # pro 由外部注入（测试）或由 token 初始化（生产）；token 检查仅在真初始化时生效。
        if pro is not None:
            self._pro = pro
        else:
            token = self.settings.tushare_token.strip()
            if not token:
                raise TushareTokenError("未配置 TUSHARE_TOKEN，请在 .env 填入（注册见 https://tushare.pro ）。")
            ts.set_token(token)
            self._pro = ts.pro_api()

    # ===== 核心调用：限流 + 指数退避重试 =====
    def _call(self, interface_key: str, fields: tuple[str, ...], **params: Any) -> list[dict]:
        """调用某接口，返回记录列表。vip 接口自动取 vip_api_name。"""
        api_name = get_vip_api_name(interface_key)
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._limiter.acquire()
            try:
                df = self._pro.query(api_name, fields=",".join(fields), **params)
            except Exception as exc:  # noqa: BLE001  外部 SDK 异常类型不可枚举
                last_exc = exc
                if attempt < self._max_retries:
                    self._sleep(BACKOFF_BASE_SECONDS * (2**attempt))
                    continue
                raise TushareApiError(
                    f"Tushare 调用失败（重试 {self._max_retries} 次仍报错）: {api_name} {params}"
                ) from exc
            return df.to_dict("records") if df is not None else []
        # 逻辑不可达
        raise TushareApiError(f"Tushare 调用失败: {api_name} {params}") from last_exc

    # ===== BaseFetcher 实现 =====
    def fetch_stock_list(self) -> list[StockInfo]:
        """读取全部 A 股上市公司清单（FR-DATA-02，stock_basic，list_status=L 上市）。"""
        records = self._call("stock_basic", STOCK_BASIC_FIELDS, list_status="L")
        return [
            StockInfo(
                ts_code=self._str(r.get("ts_code")),
                symbol=self._str(r.get("symbol")),
                name=self._str(r.get("name")),
                industry=self._str(r.get("industry")),
                list_date=self._opt(r.get("list_date")),
            )
            for r in records
        ]

    def fetch_financials(self, ts_code: str, period: str | None = None) -> StockFeatures:
        """按 §8.1 聚合单股财务数据（FR-DATA-03/04）。

        财务三表/指标走 vip 接口；daily_basic 按贸易日取最新；补充字段（审计/质押/分红）
        各取最新一期。period=None 取最新报告期。
        """
        data: dict[str, Any] = {"ts_code": ts_code}
        fin_params: dict[str, Any] = {"ts_code": ts_code}
        if period:
            fin_params["period"] = period

        # 财务三表 + 指标（vip 接口）
        for key, fields in (
            ("income", INCOME_FIELDS),
            ("balancesheet", BALANCESHEET_FIELDS),
            ("cashflow", CASHFLOW_FIELDS),
            ("fina_indicator", FINA_INDICATOR_FIELDS),
        ):
            rec = self._latest(self._call(key, fields, **fin_params), "end_date")
            data.update(self._clean_record(rec, fields))

        # daily_basic（按 trade_date 取最新，不传 period）
        rec = self._latest(self._call("daily_basic", DAILY_BASIC_FIELDS, ts_code=ts_code), "trade_date")
        data.update(self._clean_record(rec, DAILY_BASIC_FIELDS))

        # 补充字段：审计 / 质押 / 分红（各取最新一期）
        rec = self._latest(self._call("fina_audit", FINA_AUDIT_FIELDS, ts_code=ts_code), "end_date")
        data.update(self._clean_record(rec, FINA_AUDIT_FIELDS))
        rec = self._latest(self._call("pledge_stat", PLEDGE_STAT_FIELDS, ts_code=ts_code), "end_date")
        data.update(self._clean_record(rec, PLEDGE_STAT_FIELDS))
        rec = self._latest(self._call("dividend", DIVIDEND_FIELDS, ts_code=ts_code), "end_date")
        data.update(self._clean_record(rec, DIVIDEND_FIELDS))

        model_fields = set(StockFeatures.model_fields)
        return StockFeatures(**{k: v for k, v in data.items() if k in model_fields})

    # ===== 辅助 =====
    @staticmethod
    def _latest(records: list[dict] | None, date_field: str) -> dict | None:
        """从记录列表取 date_field 最大（最新）的一条；无日期则取首条。"""
        if not records:
            return None
        dated = [r for r in records if r.get(date_field)]
        if dated:
            return max(dated, key=lambda r: r[date_field])
        return records[0]

    @staticmethod
    def _clean_record(rec: dict | None, fields: tuple[str, ...]) -> dict[str, Any]:
        """提取字段并把 NaN/None 归一化为 None（StockFeatures 容忍缺失）。"""
        out: dict[str, Any] = {}
        if not rec:
            return out
        for f in fields:
            if f in rec:
                v = rec[f]
                if isinstance(v, float) and math.isnan(v):
                    v = None
                out[f] = v
        return out

    @staticmethod
    def _str(v: Any) -> str:
        """字符串字段归一化：None/NaN → 空串。"""
        if v is None:
            return ""
        if isinstance(v, float) and math.isnan(v):
            return ""
        return str(v)

    @staticmethod
    def _opt(v: Any) -> str | None:
        """可选字符串字段归一化：NaN → None。"""
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
