from abc import ABC, abstractmethod
from pandas import DataFrame as PandasDataFrame
from typing import Literal, List, TYPE_CHECKING
from .....models.input.pydantic_pxmetadata import Measurement

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame

# Interface for data transformation
class ITransforms(ABC):
    @abstractmethod
    def wide_to_long(self, df, identifier_cols, stubnames, measurement_codes, j_column_name, sep, suffix) -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def add_sum_column(self, df: "SparkDataFrame | PandasDataFrame", sum_col_name: str, columns: List[str]) -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def merge(self, df1: "SparkDataFrame | PandasDataFrame", df2: "SparkDataFrame | PandasDataFrame", on: str, how: Literal["left", "right", "outer", "inner", "cross"] = "left") -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def rename(self, df: "SparkDataFrame | PandasDataFrame", measurement_code_by_column_name: dict) -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def add_out_value(self, df: "SparkDataFrame | PandasDataFrame", missing_cell_symbol: str) -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def add_missing_rows(self, matrix_size: int, missing_row_symbol: str, df: "SparkDataFrame | PandasDataFrame") -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def add_missing_symbolcolumns(self, measurement_codes: List[str], df: "SparkDataFrame | PandasDataFrame") -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def round_by_decimals(self, df: "SparkDataFrame | PandasDataFrame", measurements: List[Measurement]) -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def add_out_index(self, df: "SparkDataFrame | PandasDataFrame", cubemaths_helper_by_codeid: dict) -> "PandasDataFrame | SparkDataFrame":
        pass