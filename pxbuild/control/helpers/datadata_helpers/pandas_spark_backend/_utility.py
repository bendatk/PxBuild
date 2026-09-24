from abc import ABC, abstractmethod
from pandas import Series as PandasSeries, DataFrame as PandasDataFrame
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame

# Interface for utility functions
class IUtility(ABC):
    @abstractmethod
    def get_timeperiodes(self, df: "SparkDataFrame | PandasDataFrame", column_name: str) -> List[str]:
        pass

    @abstractmethod
    def get_columns_to_list(self, df: "SparkDataFrame | PandasDataFrame") -> List[str]:
        pass

    @abstractmethod
    def remove_trailing_zero_decimals(self, df: "SparkDataFrame | PandasDataFrame") -> "PandasSeries | SparkDataFrame":
        pass
