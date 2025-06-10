from .pandas_wrapper import PandasWrapper
from .spark_wrapper import SparkWrapper
from ._backend_methods import IBackendMethods

class PandasSparkBackend:

    @classmethod
    def set_backend(cls, backend: str):
        if backend not in ['pandas', 'spark']:
            raise ValueError("Backend must be either 'pandas' or 'spark'.")
        if backend == 'spark':
            cls.backend = SparkWrapper()
        else:
            cls.backend = PandasWrapper()
            
    from typing import Tuple

    @staticmethod
    def get_backend() -> "IBackendMethods":
        return PandasSparkBackend.backend