import pandas
from .abstract_datasource import AbstractDatasource
from .pandas_spark_backend._backend_methods import IBackendMethods

# Open and read the Csv file


class CsvDatasource(AbstractDatasource):
    def __init__(self, filepath: str, backend: "IBackendMethods") -> None:
        self._pandas_methods = backend
        print("Debug: Reading csv file:", filepath)
        self._df = self._pandas_methods.read_csv(filepath)

    def get_raw_data(self) -> pandas.DataFrame:
        return self._df

    def close(self) -> None:
        return super().close()
