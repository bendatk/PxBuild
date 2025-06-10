from abc import ABC, abstractmethod
from pandas import DataFrame as PandasDataFrame
from pyspark.sql import DataFrame as SparkDataFrame
from io import TextIOWrapper
from .....models.output.pxfile.keywords._data import _PxData

# Base interface for data loading and saving
class IFileIO(ABC):
    @abstractmethod
    def read_parquet(self, filepath) -> SparkDataFrame | PandasDataFrame:
        pass

    @abstractmethod
    def read_csv(self, filepath) -> SparkDataFrame | PandasDataFrame:
        pass

    @abstractmethod
    def write_pxdata_to_file(self, df: _PxData, file: TextIOWrapper, file_path: str, columns_per_line, chunk_size: int):
        pass