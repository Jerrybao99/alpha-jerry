"""特征工程字段模型与数据源抽象的纯逻辑单测（Step 1.1，Tushare 真实字段对齐）。

不触网络；验证 §8.1 需求对齐表、各接口真实字段集合、输出列为 Tushare 真实字段名、
BaseFetcher 不可实例化。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.data.base import BaseFetcher
from src.schemas.financial import (
    BALANCESHEET_FIELDS,
    CASHFLOW_FIELDS,
    DAILY_BASIC_FIELDS,
    FINA_INDICATOR_FIELDS,
    INCOME_FIELDS,
    OUTPUT_COLUMNS,
    PERCENT_FIELDS,
    REQUIREMENT_ALIGNMENT,
    STOCK_BASIC_FIELDS,
    StockFeatures,
    StockInfo,
    requirement_coverage,
)


def test_requirement_alignment_covers_all_55() -> None:
    """§8.1 共 55 个需求字段，对齐表必须全覆盖且中文名唯一。"""
    reqs = [a.requirement for a in REQUIREMENT_ALIGNMENT]
    assert len(reqs) == 55
    assert len(set(reqs)) == 55


def test_requirement_match_types_valid() -> None:
    """match 取值合法；exact/approximate 必须有 tushare_field，其余必须无。"""
    valid = {"exact", "approximate", "computed_in_scoring", "unavailable"}
    for a in REQUIREMENT_ALIGNMENT:
        assert a.match in valid, a
        if a.match in {"exact", "approximate"}:
            assert a.tushare_field, f"{a.match} 缺少字段: {a.requirement}"
        else:
            assert a.tushare_field is None, f"{a.match} 不应有字段: {a.requirement}"


def test_requirement_coverage_summary() -> None:
    """覆盖统计：exact 占多数，unavailable 受控。"""
    cov = requirement_coverage()
    assert sum(cov.values()) == 55
    assert cov["exact"] >= 35
    assert cov["unavailable"] == 5  # 调整后每股净资产/A股/B股/国家持股/国有法人持股
    assert cov["computed_in_scoring"] == 6


def test_endpoint_field_lists_no_duplicate() -> None:
    """各接口字段集内部无重复，且含 ts_code 主键（daily_basic 例外也含）。"""
    for fields in (
        STOCK_BASIC_FIELDS,
        INCOME_FIELDS,
        BALANCESHEET_FIELDS,
        CASHFLOW_FIELDS,
        FINA_INDICATOR_FIELDS,
        DAILY_BASIC_FIELDS,
    ):
        assert len(fields) == len(set(fields)), fields
        assert "ts_code" in fields


def test_output_columns_are_tushare_real_names() -> None:
    """输出列全部为 Tushare 真实字段名，ts_code 置首，无中文名/无自造字段。"""
    cols = list(OUTPUT_COLUMNS)
    assert cols[0] == "ts_code"
    assert len(cols) == len(set(cols))  # 无重复
    # 抽查关键真实字段名存在（对齐官方文档）
    for f in (
        "n_income_attr_p",
        "undistr_porfit",
        "total_hldr_eqy_exc_min_int",
        "n_cash_flows_fnc_act",
        "grossprofit_margin",
        "debt_to_assets",
        "ocf_to_shortdebt",
        "float_share",
    ):
        assert f in cols, f
    # StockFeatures.output_columns() 与 OUTPUT_COLUMNS 一致
    assert StockFeatures.output_columns() == cols


def test_output_columns_match_model_fields() -> None:
    """输出列必须是 StockFeatures 已声明字段，保证写盘不缺列。"""
    declared = set(StockFeatures.model_fields)
    assert set(OUTPUT_COLUMNS) <= declared


def test_percent_fields_subset_of_output() -> None:
    """百分比字段必须是输出列。"""
    assert PERCENT_FIELDS <= set(OUTPUT_COLUMNS)


def test_stock_features_required_ts_code() -> None:
    """ts_code 必填，缺失报错。"""
    with pytest.raises(ValidationError):
        StockFeatures()  # type: ignore[call-arg]


def test_stock_features_real_field_roundtrip() -> None:
    """用 Tushare 真实字段名构造与 dump，字段名保持不变（无 alias 改名）。"""
    feat = StockFeatures(
        ts_code="600000.SH",
        symbol="600000",
        name="浦发银行",
        revenue=1.2e10,
        n_income_attr_p=3.4e9,
        roe=12.5,
        float_share=2.9e10,
    )
    dumped = feat.model_dump()
    assert dumped["ts_code"] == "600000.SH"
    assert dumped["n_income_attr_p"] == 3.4e9
    assert dumped["float_share"] == 2.9e10
    # dump 的键即 Tushare 真实字段名，可直接作为 CSV 表头
    assert set(dumped) >= set(OUTPUT_COLUMNS)


def test_stock_features_tolerates_missing() -> None:
    """缺失字段默认 None（采集时单股可能缺字段）。"""
    feat = StockFeatures(ts_code="000001.SZ")
    dumped = feat.model_dump()
    assert dumped["n_income_attr_p"] is None
    assert dumped["eps"] is None


def test_stock_info_real_fields() -> None:
    info = StockInfo(ts_code="600000.SH", symbol="600000", name="浦发银行", industry="银行", list_date="19991110")
    assert info.ts_code == "600000.SH"
    assert info.symbol == "600000"


def test_base_fetcher_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseFetcher()  # type: ignore[abstract]


def test_base_fetcher_concrete_subclass_works() -> None:
    """完整实现的子类可正常实例化；fetch_financials 用 ts_code 返回 StockFeatures。"""

    class FakeFetcher(BaseFetcher):
        def fetch_stock_list(self):
            return [StockInfo(ts_code="600000.SH", symbol="600000", name="浦发银行")]  # noqa: ARG002

        def fetch_financials(self, ts_code, period=None):
            return StockFeatures(ts_code=ts_code)

    f = FakeFetcher()
    assert f.fetch_stock_list()[0].ts_code == "600000.SH"
    assert f.fetch_financials("600000.SH").ts_code == "600000.SH"
