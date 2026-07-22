"""采集主流程编排（Step 1.3，FR-DATA-05/06）。

读全量清单 → 低并发线程池采集（concurrency 来自 Settings）→ 缓存原始响应 →
字段标准化为 StockFeatures；单股失败隔离，记入失败清单并落 ``data/fin/YYMMDD-失败.xlsx``。

设计要点：
- 只依赖 ``BaseFetcher`` 抽象，换数据源不改本编排（§6.3 原则 3）。
- 线程池并发数 = ``Settings.concurrency``，避免一次性打满限流（FR-DATA-06）。
- 缓存键 = ts_code + period，同季重跑不重复调接口（FR-DATA-06）。
- 单股异常被捕获入失败清单，不拖垮整体（FR-DATA-05 / NFR-04）。
"""

from __future__ import annotations

import datetime as _dt
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from src.config import Settings, get_settings
from src.data.base import BaseFetcher
from src.schemas.financial import StockFeatures
from src.utils.cache import Cache
from src.utils.format import to_output_row

logger = logging.getLogger(__name__)


@dataclass
class Failure:
    """单股采集失败记录（审计可追溯）。"""

    ts_code: str
    name: str
    error: str


@dataclass
class CollectionResult:
    """采集结果：成功特征列表 + 失败清单 + 命中缓存数。"""

    successes: list[StockFeatures] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)
    cached_hits: int = 0
    total: int = 0

    @property
    def success_count(self) -> int:
        return len(self.successes)

    @property
    def failure_count(self) -> int:
        return len(self.failures)


class CollectionPipeline:
    """采集编排器。executor 可注入便于单测（用顺序执行器避免真实线程）。"""

    def __init__(
        self,
        fetcher: BaseFetcher,
        settings: Settings | None = None,
        cache: Cache | None = None,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self.fetcher = fetcher
        self.settings = settings or get_settings()
        self.cache = cache if cache is not None else Cache(self.settings.data_root / "cache")
        self._owns_executor = executor is None
        self._executor = executor or ThreadPoolExecutor(max_workers=max(1, self.settings.concurrency))

    def run(self, period: str | None = None, codes: list[str] | None = None) -> CollectionResult:
        """执行采集。codes 非空时只采指定股票（冒烟测试用）。

        Returns:
            CollectionResult（成功 + 失败 + 缓存命中数）。
        """
        stocks = self.fetcher.fetch_stock_list()
        if codes:
            wanted = set(codes)
            stocks = [s for s in stocks if s.ts_code in wanted]
        result = CollectionResult(total=len(stocks))
        name_map = {s.ts_code: s.name for s in stocks}

        futures = {self._executor.submit(self._fetch_one, s.ts_code, period): s.ts_code for s in stocks}
        for fut in futures:
            ts_code = futures[fut]
            try:
                features, hit = fut.result()
            except Exception as exc:  # noqa: BLE001  单股失败隔离，原因记入审计
                logger.warning("采集失败 %s: %s", ts_code, exc)
                result.failures.append(Failure(ts_code, name_map.get(ts_code, ""), str(exc)))
                continue
            if hit:
                result.cached_hits += 1
            if features is not None:
                result.successes.append(features)
            else:
                result.failures.append(Failure(ts_code, name_map.get(ts_code, ""), "无数据"))
        return result

    def _fetch_one(self, ts_code: str, period: str | None) -> tuple[StockFeatures | None, bool]:
        """采集单股：先查缓存，未命中再调接口并回写缓存。返回 (特征, 是否命中缓存)。"""
        cached = self.cache.get(ts_code, period)
        if cached is not None:
            return cached, True
        features = self.fetcher.fetch_financials(ts_code, period)
        if features is None:
            return None, False
        self.cache.set(ts_code, period, features)
        return features, False

    def to_rows(self, result: CollectionResult) -> list[dict[str, Any]]:
        """把成功特征标准化为输出行（§8.1 字段顺序 + 百分比格式化）。"""
        return [to_output_row(f) for f in result.successes]

    def write_failures(self, failures: list[Failure], date: _dt.date | None = None) -> Path:
        """失败清单落 ``data/fin/YYMMDD-失败.xlsx``（审计可追溯，FR-DATA-05）。"""
        date = date or _dt.date.today()
        out = self.settings.data_path("fin") / f"{date.strftime('%y%m%d')}-失败.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "失败"
        ws.append(["ts_code", "name", "error"])
        for f in failures:
            ws.append([f.ts_code, f.name, f.error])
        wb.save(out)
        return out

    def close(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=False)

    def __enter__(self) -> CollectionPipeline:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
