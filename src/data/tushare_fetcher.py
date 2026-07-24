"""Tushare 数据源适配器。实现 BaseFetcher，含限流器（每分钟调用上限）与指数退避重试（1s/2s/4s）。
财务四表等优先用 _vip 接口；token 从 Settings 读取注入 SDK，空则报错提示配置 .env。
"""
from __future__ import annotations

import csv
import math
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tushare as ts

from src.config import Settings, get_settings
from src.data.base import BaseFetcher
from src.data.interfaces import get_vip_api_name
from src.rating.industry import sw_l2_to_category
from src.schemas.financial import (
    BALANCESHEET_FIELDS,
    CASHFLOW_FIELDS,
    FINA_INDICATOR_FIELDS,
    INCOME_FIELDS,
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
        return self._call_raw(api_name, fields=",".join(fields), **params)

    def _call_raw(self, api_name: str, **params: Any) -> list[dict]:
        """底层调用 Tushare API，限流 + 指数退避重试。"""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._limiter.acquire()
            try:
                df = self._pro.query(api_name, **params)
            except Exception as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    self._sleep(BACKOFF_BASE_SECONDS * (2**attempt))
                    continue
                raise TushareApiError(
                    f"Tushare 调用失败（重试 {self._max_retries} 次仍报错）: {api_name} {params}"
                ) from exc
            return df.to_dict("records") if df is not None else []
        raise TushareApiError(f"Tushare 调用失败: {api_name} {params}") from last_exc

    def _call_no_fields(self, interface_key: str, **params: Any) -> list[dict]:
        """调用接口不传 fields（返回全部默认字段），限流 + 退避。"""
        return self._call_raw(get_vip_api_name(interface_key), **params)

    # ===== BaseFetcher 实现 =====
    def fetch_stock_list(self) -> list[StockInfo]:
        """读取全部 A 股上市公司清单，行业字段保留 stock_basic 原始值。
        SW 分类由 ``_enrich_with_sw_category`` 在后续按需调用。
        """
        records = self._call("stock_basic", STOCK_BASIC_FIELDS, list_status="L")
        return [
            StockInfo(
                ts_code=self._str(r.get("ts_code")),
                symbol=self._str(r.get("symbol")),
                name=self._str(r.get("name")),
                industry=self._str(r.get("industry")),
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

        # income 设定报告期（end_date 来自利润表，是「财报所属期间」的唯一权威来源）。
        rec = self._latest(self._call("income", INCOME_FIELDS, **fin_params), "end_date")
        data.update(self._clean_record(rec, INCOME_FIELDS))
        # report_period 锁定后，其余接口仍按各自 end_date 选最新记录，但不覆盖该字段
        # （pledge_stat/fina_audit 的 end_date 是统计截止日/审计对应年报，语义不同）。
        _no_end_date = {"end_date"}

        # 资产负债表 / 现金流量表 / 财务指标（vip 接口）
        for key, fields in (
            ("balancesheet", BALANCESHEET_FIELDS),
            ("cashflow", CASHFLOW_FIELDS),
            ("fina_indicator", FINA_INDICATOR_FIELDS),
        ):
            rec = self._latest(self._call(key, fields, **fin_params), "end_date")
            data.update(self._clean_record(rec, fields, exclude=_no_end_date))

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
    def _clean_record(rec: dict | None, fields: tuple[str, ...], *, exclude: set[str] | None = None) -> dict[str, Any]:
        """提取字段并把 NaN/None 归一化为 None（StockFeatures 容忍缺失）。

        exclude 中的字段不写入返回字典（用于保护 income 确定的报告期 end_date 不被覆盖）。
        """
        out: dict[str, Any] = {}
        if not rec:
            return out
        exclude = exclude or set()
        for f in fields:
            if f in exclude:
                continue
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

    # ===== 申万行业分类 =====
    _SW_MEMBER_FIELDS: tuple[str, ...] = ("ts_code", "l1_name", "l2_name", "l3_name", "is_new")

    def _sw_cache_path(self) -> Path:
        return self.settings.data_root / "cache" / "sw_industry.csv"

    @staticmethod
    def _sw_name_to_category(rec: dict, default: str = "未分类") -> str:
        """从 index_member_all 记录中按 l2_name > l1_name > l3_name 优先级取分类。"""
        for key in ("l2_name", "l1_name", "l3_name"):
            name = str(rec.get(key, "")).strip()
            if name:
                cat = sw_l2_to_category(name)
                if cat != "未分类":
                    return cat
                # 对于一级/三级行业名也试映射（部分 SW L1/L3 名和 L2 名重叠）
        return default

    def _fetch_one_sw_category(self, ts_code: str) -> str:
        """查单股申万行业 → 五大类。不传 fields，获取全部默认字段（含 l1/l2/l3_name）。"""
        try:
            records = self._call_no_fields("index_member_all", ts_code=ts_code, is_new="Y")
        except TushareApiError:
            return "未分类"
        for r in records:
            cat = self._sw_name_to_category(r)
            if cat != "未分类":
                return cat
        return "未分类"

    def build_sw_cache(self) -> dict[str, str]:
        """构建全量 SW 缓存（首次慢，约 5000+ API 调用），之后读缓存秒过。
        一般不需要主动调用；``_enrich_with_sw_category`` 会按需查 API 并增量写缓存。
        """
        all_codes = self._call("stock_basic", ("ts_code",), list_status="L")
        mapping: dict[str, str] = {}
        for r in all_codes:
            ts_code = self._str(r.get("ts_code"))
            if not ts_code:
                continue
            mapping[ts_code] = self._fetch_one_sw_category(ts_code)
        self._save_sw_cache(mapping)
        return mapping

    def _save_sw_cache(self, mapping: dict[str, str]) -> None:
        """落盘 sw_industry.csv。"""
        cache_path = self._sw_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["ts_code", "l2_name", "category"])
            for ts_code in sorted(mapping):
                writer.writerow([ts_code, "", mapping[ts_code]])

    @staticmethod
    def load_sw_cache(cache_path: Path) -> dict[str, str] | None:
        """从 CSV 加载申万行业缓存，返回 {ts_code → category}；文件不存在或损坏返回 None。"""
        if not cache_path.exists():
            return None
        try:
            text = cache_path.read_text(encoding="utf-8-sig")
        except OSError:
            return None
        mapping: dict[str, str] = {}
        for row in csv.reader(text.splitlines()):
            if not row or row[0] == "ts_code":
                continue
            if len(row) >= 3 and row[0] and row[2]:
                mapping[row[0].strip()] = row[2].strip()
        return mapping if mapping else None

    def _load_or_build_sw_cache(self) -> dict[str, str]:
        """加载 SW 行业缓存，不存在返回空 dict（按需查询增量填充）。"""
        cache_path = self._sw_cache_path()
        mapping = self.load_sw_cache(cache_path)
        return mapping if mapping is not None else {}

    def _enrich_with_sw_category(self, stocks: list[StockInfo]) -> list[StockInfo]:
        """用申万行业→五大类替换 stock_basic 的 industry。按需查 API，增量写缓存。"""
        sw_map = self._load_or_build_sw_cache()
        modified = False
        for s in stocks:
            if s.ts_code not in sw_map:
                sw_map[s.ts_code] = self._fetch_one_sw_category(s.ts_code)
                modified = True
            cat = sw_map.get(s.ts_code)
            if cat and cat != "未分类":
                s.industry = cat
        if modified:
            self._save_sw_cache(sw_map)
        return stocks
