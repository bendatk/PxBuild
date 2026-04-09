from abc import ABC, abstractmethod
from pandas import DataFrame as PandasDataFrame
from io import BufferedWriter, TextIOWrapper
from .....models.output.pxfile.keywords._data import _PxData
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame

# Base interface for data loading and saving
class IFileIO(ABC):
    @abstractmethod
    def read_parquet(self, filepath) -> "SparkDataFrame | PandasDataFrame":
        pass

    @abstractmethod
    def read_csv(self, filepath) -> "SparkDataFrame | PandasDataFrame":
        pass

    @abstractmethod
    def write_pxdata_to_file(self, df: _PxData, file: TextIOWrapper | BufferedWriter, file_path: str, columns_per_line):
        pass