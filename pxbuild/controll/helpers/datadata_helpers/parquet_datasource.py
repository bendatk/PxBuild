import pyarrow.parquet as pq, pandas
from .abstract_datasource import AbstractDatasource
from ...helpers.logger_config import logger
from .pandas_spark_backend.pandas_spark_backend import PandasSparkBackend
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame

# Open and read the Parquet file


class ParquetDatasource(AbstractDatasource):
    def __init__(self, filepath: str) -> None:
        self._filepath = filepath
        logger.debug(f"Reading parquet file: {filepath}")
        self._parquet_file = pq.ParquetFile(filepath)
        self._backend = PandasSparkBackend.get_backend()

    def get_raw_data(self) -> "pandas.DataFrame | SparkDataFrame":
        if self._parquet_file:
            self.raw_data = self._backend.read_parquet(self._parquet_file)
        return self.raw_data

    def close(self) -> None:
        self._parquet_file = None