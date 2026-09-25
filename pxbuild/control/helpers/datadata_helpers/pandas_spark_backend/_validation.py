from abc import ABC, abstractmethod
#from pandas import DataFrame as PandasDataFrame
import pandas as pd
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame as SparkDataFrame

# Interface for validation
class IValidation(ABC):
    @abstractmethod
    def validate_data(self, df: "Union[SparkDataFrame, pd.DataFrame]", data_file_path: str) -> None:
        pass

    @abstractmethod
    def validate_coded_values(self, df: "Union[SparkDataFrame, pd.DataFrame]", column: str, codelist: list) -> None:
        pass

    @abstractmethod
    def validate_codelist_vs_data_values(self, df: "Union[SparkDataFrame, pd.DataFrame]", coded_dimensions: list, resolved_pxcodes_ids: dict) -> None:
        pass