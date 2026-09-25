"""Spark backend smoke tests.

Run only inside Azure Databricks (a live Spark session is required), via::

    uv run pytest -m databricks tests/spark

Not run locally or in GitHub Actions CI (see pyproject.toml addopts and
tests/spark/conftest.py).
"""

from pathlib import Path
from unittest.mock import Mock

from pxbuild.control.helpers.datadata_helpers.pandas_spark_backend.pandas_spark_backend import (
    create_backend,
)
from pxbuild.control.helpers.datadata_helpers.pandas_spark_backend.spark_wrapper import (
    SparkWrapper,
)


def test_create_backend_returns_spark_wrapper():
    backend = create_backend("spark")

    assert isinstance(backend, SparkWrapper)
    assert backend.backend_name == "spark"


def test_temp_output_path_uses_configured_volume(monkeypatch):
    monkeypatch.setenv("PXBUILD_SPARK_TEMP_VOLUME", "/Volumes/catalog/schema/volume/")

    temp_path = SparkWrapper.get_temp_output_path("/tmp/output")

    assert temp_path.startswith("/Volumes/catalog/schema/volume/pxbuild-")


def test_temp_output_path_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("PXBUILD_SPARK_TEMP_VOLUME", raising=False)

    assert SparkWrapper.get_temp_output_path("/tmp/output") == "/tmp/output"


def test_trim_trailing_whitespace(tmp_path):
    data_file = Path(tmp_path) / "part-00000.txt"
    data_file.write_bytes(b"first line\nlast line \n")

    SparkWrapper.trim_trailing_whitespace(str(data_file))

    assert data_file.read_bytes() == b"first line\nlast line"


def test_read_csv_uses_string_columns_and_semicolon_separator(monkeypatch):
    spark = Mock()
    options = spark.read.option.return_value.option.return_value.option.return_value
    options.csv.return_value = Mock()
    monkeypatch.setattr(SparkWrapper, "get_spark", staticmethod(lambda: spark))

    backend = object.__new__(SparkWrapper)
    result = backend.read_csv("input.csv")

    spark.read.option.assert_any_call("header", True)
    spark.read.option.return_value.option.assert_any_call("sep", ";")
    spark.read.option.return_value.option.return_value.option.assert_called_once_with("inferSchema", False)
    options.csv.assert_called_once_with("input.csv")
    assert result is options.csv.return_value


def test_get_spark_returns_a_usable_session():
    spark = SparkWrapper.get_spark()

    # A trivial round trip through Spark confirms the session actually
    # works, not just that it was constructed.
    df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "value"])
    assert df.count() == 2
    assert sorted(row["value"] for row in df.collect()) == ["a", "b"]
