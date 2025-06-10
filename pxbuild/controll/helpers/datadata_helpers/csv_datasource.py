import pandas
from typing import Union
from .abstract_datasource import AbstractDatasource
from .pandas_spark_backend.pandas_spark_backend import PandasSparkBackend

# Open and read the Csv file


class CsvDatasource(AbstractDatasource):
    def __init__(self, filepath: str) -> None:
        self._pandas_methods = PandasSparkBackend.get_backend()
        print("Debug: Reading csv file:", filepath)
        self._df = self._pandas_methods.read_csv(filepath)


    def get_raw_data(self) -> pandas.DataFrame:
        return self._df
    
    def close(self) -> None:
        return super().close()
