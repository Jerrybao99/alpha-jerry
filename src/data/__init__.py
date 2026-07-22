"""数据源适配包。

对外暴露抽象接口、接口注册表、字段模型与 Tushare 适配器（Step 1.2）。
"""

from src.data.base import BaseFetcher
from src.data.interfaces import TUSHARE_INTERFACES, TushareInterface, get_doc_url, get_vip_api_name
from src.data.tushare_fetcher import RateLimiter, TushareApiError, TushareFetcher, TushareTokenError
from src.schemas.financial import StockFeatures, StockInfo

__all__ = [
    "BaseFetcher",
    "RateLimiter",
    "StockFeatures",
    "StockInfo",
    "TUSHARE_INTERFACES",
    "TushareApiError",
    "TushareFetcher",
    "TushareInterface",
    "TushareTokenError",
    "get_doc_url",
    "get_vip_api_name",
]
