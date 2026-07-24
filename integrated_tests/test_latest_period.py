"""最新报告期交叉校验（network）。跑 2 股真实冒烟后，独立重查 Tushare 比对 CSV。

标 @pytest.mark.network，CI 跳过；本地 `uv run pytest -m network -k latest` 运行。
无 TUSHARE_TOKEN 时 skip。
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest
import tushare as ts

from scripts.smoke_collect import run_smoke
from scripts.verify_latest import verify_csv
from src.config import Settings
from src.data.tushare_fetcher import TushareFetcher
from src.utils.period import expected_latest_period


@pytest.mark.network
def test_latest_period_cross_check(tmp_path: Path) -> None:
    """2 股真实采集 → CSV 的 end_date 与 Tushare 独立重查一致且不陈旧。"""
    settings = Settings(data_dir=str(tmp_path))
    token = settings.tushare_token.strip()
    if not token:
        pytest.skip("未配置 TUSHARE_TOKEN")
    fetcher = TushareFetcher(settings)
    out = tmp_path / "test"
    feat_path, _, ok, fail = run_smoke(fetcher, settings, 2, out, date=_dt.date(2026, 7, 24), seed=1)
    assert ok == 2 and fail == 0, "冒烟采集未全部成功"

    ts.set_token(token)
    pro = ts.pro_api()
    results = verify_csv(pro, feat_path, today=_dt.date(2026, 7, 24))
    assert results, "未读到 CSV 数据行"

    expected = expected_latest_period(_dt.date(2026, 7, 24))
    for r in results:
        assert r["ok_end"], f"{r['ts_code']} end_date CSV={r['csv_end_date']} != Tushare={r['tushare_end_date']}"
        assert r["ok_fresh"], f"{r['ts_code']} end_date {r['csv_end_date']} 早于预期最新报告期 {expected}"
