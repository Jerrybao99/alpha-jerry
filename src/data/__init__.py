"""数据源适配包。

对外暴露抽象接口与字段模型；具体实现（TushareFetcher）在 Step 1.2 加入。
"""

from src.data.base import BaseFetcher
from src.schemas.financial import StockFeatures, StockInfo

__all__ = ["BaseFetcher", "StockFeatures", "StockInfo"]
