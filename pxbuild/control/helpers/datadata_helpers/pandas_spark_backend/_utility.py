from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pandas import DataFrame as PandasDataFrame
from pandas import Series as PandasSeries

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame


# Interface for utility functions
class IUtility(ABC):
    @abstractmethod
    def get_timeperiodes(self, df: "SparkDataFrame | PandasDataFrame", column_name: str) -> list[str]:
        pass

    @abstractmethod
    def get_columns_to_list(self, df: "SparkDataFrame | PandasDataFrame") -> list[str]:
        pass

    @abstractmethod
    def count_rows(self, data: "SparkDataFrame | PandasSeries") -> int:
        pass

    @abstractmethod
    def remove_trailing_zero_decimals(self, df: "SparkDataFrame | PandasDataFrame") -> "PandasSeries | SparkDataFrame":
        pass
