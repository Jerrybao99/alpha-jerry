"""数据源抽象接口（dev-guide §6.3 原则 3：数据源单一真源 + Fallback）。

先定义"接口"再写"实现"：TushareFetcher（Step 1.2）及其他未来数据源
（同花顺 / akshare ...）均实现 BaseFetcher；业务代码（pipeline / DataAgent）
只依赖本抽象，换源不改业务代码。

字段溯源与 Tushare 真实字段对齐，见 src.schemas.financial.TUSHARE_FIELD_MAP。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.schemas.financial import StockFeatures, StockInfo


class BaseFetcher(ABC):
    """数据源适配器抽象基类。

    约束：
    - 业务代码只依赖本抽象，禁止直接 import 具体数据源 SDK（FR-DATA-01）。
    - 实现类负责限流 / 重试 / 缓存（FR-DATA-06/07），本接口只声明能力。
    - 主键统一用 ts_code（如 "600000.SH"），与 Tushare 接口一致。
    """

    @abstractmethod
    def fetch_stock_list(self) -> list[StockInfo]:
        """读取全部 A 股上市公司清单（FR-DATA-02，来源 stock_basic）。

        返回每只股票的 ts_code、code(=symbol)、name、industry、list_date。
        """

    @abstractmethod
    def fetch_financials(self, ts_code: str, period: str | None = None) -> StockFeatures:
        """按 §8.1 需求采集单股财务数据（FR-DATA-03）。

        实现需聚合 income / balancesheet / cashflow / fina_indicator / daily_basic
        多个接口的真实字段，按 OUTPUT_COLUMNS 输出；§8.1 中的计算型需求
        （股东权益比/主营利润率等）不在此采集，留给评分纯函数计算。
        period=None 表示取最新报告期（FR-DATA-04）。

        Args:
            ts_code: Tushare 股票代码，如 "600000.SH"。
            period: 财报所属期间，如 "20251231"；None 取最新报告期。

        Returns:
            该股票的特征数据（字段名即 Tushare 真实字段名，数据为真实值）。
        """
