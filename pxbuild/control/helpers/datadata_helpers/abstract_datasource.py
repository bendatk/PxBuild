from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pandas import DataFrame as PandasDataFrame

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame


class AbstractDatasource(ABC):
    @abstractmethod
    def get_raw_data(self) -> "PandasDataFrame | SparkDataFrame":
        pass

    @abstractmethod
    def close(self) -> None:
        pass
