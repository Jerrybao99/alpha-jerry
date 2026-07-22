"""Step 1.4 冒烟采集集成测试。mock 数据源验证两张 CSV 落地与格式化
（中文列头/百分比/亿万/CJK 对齐/数据来源表）。不触网络。
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from scripts.smoke_collect import run_smoke
from src.config import Settings
from src.schemas.financial import StockFeatures, StockInfo


class _FakeFetcher:
    def __init__(self, features: dict[str, StockFeatures]) -> None:
        self.features = features

    def fetch_stock_list(self) -> list[StockInfo]:
        return [StockInfo(ts_code=c, symbol=c.split(".")[0], name=c) for c in sorted(self.features)]

    def fetch_financials(self, ts_code, period=None):
        return StockFeatures(**self.features[ts_code].model_dump())


def _settings(data_dir: Path) -> Settings:
    return Settings(tushare_token="t", data_dir=str(data_dir), concurrency=2)


def _feat(ts_code: str) -> StockFeatures:
    return StockFeatures(
        ts_code=ts_code,
        symbol=ts_code.split(".")[0],
        name=ts_code,
        industry="银行",
        list_date="19991110",
        end_date="20241231",
        revenue=1.5e10,  # 150亿
        n_income_attr_p=3.4e9,  # 34亿
        roe=12.5,
        netprofit_yoy=20.0,  # 百分比
        total_mv=3.2e6,  # 320万
        audit_result="标准无保留意见",
    )


def test_smoke_writes_two_csvs(tmp_path: Path) -> None:
    fetcher = _FakeFetcher({c: _feat(c) for c in ("600000.SH", "000001.SZ", "000002.SZ")})
    out = tmp_path / "test"
    feat_path, src_path, ok, fail = run_smoke(
        fetcher, _settings(tmp_path), sample=2, out_dir=out, date=_dt.date(2026, 7, 23), seed=1
    )
    assert ok == 2 and fail == 0
    assert feat_path.name == "260723.csv"
    assert src_path.name == "260723-数据来源.csv"
    assert feat_path.exists() and src_path.exists()


def test_features_csv_chinese_header_and_format(tmp_path: Path) -> None:
    fetcher = _FakeFetcher({"600000.SH": _feat("600000.SH"), "000001.SZ": _feat("000001.SZ")})
    out = tmp_path / "test"
    feat_path, _, _, _ = run_smoke(fetcher, _settings(tmp_path), 2, out, date=_dt.date(2026, 7, 23))
    text = feat_path.read_text(encoding="utf-8-sig")
    lines = text.strip().split("\n")
    header = lines[1]  # 第一行是 BOM+header；split 后首行含 BOM，取首行即可
    header = lines[0].lstrip("\ufeff")
    # 中文列头存在
    assert "股票代码(ts_code)" in header
    assert "营业收入" in header
    # 百分比带 % 两位小数
    assert "20.00%" in text
    # 大数用亿/万（非科学计数法）
    assert "150.00亿" in text
    assert "34.00亿" in text
    # 无科学计数法
    assert "e+" not in text.lower() and "E+" not in text


def test_features_csv_cells_aligned(tmp_path: Path) -> None:
    """同一列（除最后一列外）所有行显示宽度一致（CJK 感知对齐；最后一列不填充）。"""
    from src.reports.csv_writer import display_width

    fetcher = _FakeFetcher({"600000.SH": _feat("600000.SH"), "000001.SZ": _feat("000001.SZ")})
    out = tmp_path / "test"
    feat_path, _, _, _ = run_smoke(fetcher, _settings(tmp_path), 2, out, date=_dt.date(2026, 7, 23))
    text = feat_path.read_text(encoding="utf-8-sig")
    if text.endswith("\n"):
        text = text[:-1]
    lines = text.split("\n")
    lines[0] = lines[0].lstrip("\ufeff")
    fields = [ln.split(",") for ln in lines]
    n_cols = len(fields[0])
    for col in range(n_cols - 1):  # 最后一列不填充，跳过
        widths = {display_width(row[col]) for row in fields}
        assert len(widths) == 1, f"列 {col} 未对齐: {widths}"


def test_data_source_csv_content(tmp_path: Path) -> None:
    fetcher = _FakeFetcher({"600000.SH": _feat("600000.SH")})
    out = tmp_path / "test"
    _, src_path, _, _ = run_smoke(fetcher, _settings(tmp_path), 1, out, date=_dt.date(2026, 7, 23))
    text = src_path.read_text(encoding="utf-8-sig")
    assert text.startswith("接口,字段,字段中文,文档URL")
    # 含 vip 接口名与文档 URL
    assert "income_vip" in text
    assert "https://tushare.pro/document/2?doc_id=" in text
    # 每行 4 列
    for ln in text.strip().split("\n")[1:]:
        assert ln.count(",") == 3


def test_smoke_sample_clamped(tmp_path: Path) -> None:
    """采样数超过清单时自动收敛到清单大小。"""
    fetcher = _FakeFetcher({"600000.SH": _feat("600000.SH")})
    out = tmp_path / "test"
    _, _, ok, _ = run_smoke(fetcher, _settings(tmp_path), 5, out, date=_dt.date(2026, 7, 23))
    assert ok == 1
