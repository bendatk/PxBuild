import pandas
from .abstract_datasource import AbstractDatasource

class PandasDatasource(AbstractDatasource):
    def __init__(self, dataframe: "pandas.DataFrame") -> None:
        from pandas import DataFrame as PandasDataFrame
        self._dataframe: PandasDataFrame = dataframe

    def get_raw_data(self) -> "pandas.DataFrame":
        return self._dataframe

    def close(self) -> None:
        pass