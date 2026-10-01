from ._backend_methods import IBackendMethods
from .pandas_wrapper import PandasWrapper
from .spark_wrapper import SparkWrapper


def create_backend(backend: str) -> "IBackendMethods":
    """Create a fresh backend instance for the requested engine.

    This replaces the old ``PandasSparkBackend`` singleton: callers must
    hold on to the returned instance and pass it explicitly to whatever
    needs it, instead of relying on process-global state.
    """
    if backend == "spark":
        return SparkWrapper()
    elif backend == "pandas":
        return PandasWrapper()
    else:
        raise ValueError("Backend must be either 'pandas' or 'spark'.")
