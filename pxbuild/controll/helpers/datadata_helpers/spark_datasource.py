import pyarrow.parquet as pq, pandas
from .abstract_datasource import AbstractDatasource
from ...helpers.logger_config import logger
from .pandas_spark_backend.pandas_spark_backend import PandasSparkBackend
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame

class SparkDatasource(AbstractDatasource):
    def __init__(self, dataframe: "SparkDataFrame") -> None:
        from pyspark.sql import DataFrame as SparkDataFrame
        self._dataframe: SparkDataFrame = dataframe

    def get_raw_data(self) -> "SparkDataFrame":
        return self._dataframe

    def close(self) -> None:
        pass