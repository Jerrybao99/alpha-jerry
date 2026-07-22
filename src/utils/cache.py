"""采集缓存。按 ts_code + period 缓存 StockFeatures，避免同季重复调接口。
本地 JSON 文件存储，缓存目录由 Settings 派生，不硬编码。
"""

from __future__ import annotations

import json
from pathlib import Path

from src.schemas.financial import StockFeatures


class Cache:
    """本地文件缓存。disabled 时 get 永远返回 None、set 不写盘。"""

    def __init__(self, cache_dir: Path, enabled: bool = True) -> None:
        self.cache_dir = cache_dir
        self.enabled = enabled
        if enabled:
            cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key_for(ts_code: str, period: str | None) -> str:
        """缓存键：ts_code + period；period 为 None 记 ``latest``。"""
        return f"{ts_code}_{period or 'latest'}".replace("/", "_")

    def _path(self, ts_code: str, period: str | None) -> Path:
        return self.cache_dir / f"{self.key_for(ts_code, period)}.json"

    def get(self, ts_code: str, period: str | None) -> StockFeatures | None:
        """命中返回 StockFeatures，未命中/损坏返回 None。"""
        if not self.enabled:
            return None
        path = self._path(ts_code, period)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return StockFeatures(**data)

    def set(self, ts_code: str, period: str | None, features: StockFeatures) -> None:
        """写入缓存（disabled 时跳过）。"""
        if not self.enabled:
            return
        self._path(ts_code, period).write_text(features.model_dump_json(), encoding="utf-8")
