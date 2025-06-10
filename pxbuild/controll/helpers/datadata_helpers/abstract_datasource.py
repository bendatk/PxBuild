from abc import ABC, abstractmethod
from pyspark.sql import DataFrame as SparkDataFrame
from pandas import DataFrame as PandasDataFrame

class AbstractDatasource(ABC):
    @abstractmethod
    def get_raw_data(self) -> PandasDataFrame | SparkDataFrame:
        pass

    @abstractmethod
    def close(self) -> None:
        pass