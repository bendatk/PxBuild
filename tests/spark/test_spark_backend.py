"""Spark backend smoke tests.

Run only inside Azure Databricks (a live Spark session is required), via::

    uv run pytest -m databricks tests/spark

Not run locally or in GitHub Actions CI (see pyproject.toml addopts and
tests/spark/conftest.py).
"""

from pxbuild.controll.helpers.datadata_helpers.pandas_spark_backend.pandas_spark_backend import (
    create_backend,
)
from pxbuild.controll.helpers.datadata_helpers.pandas_spark_backend.spark_wrapper import (
    SparkWrapper,
)


def test_create_backend_returns_spark_wrapper():
    backend = create_backend("spark")

    assert isinstance(backend, SparkWrapper)
    assert backend.backend_name == "spark"


def test_get_spark_returns_a_usable_session():
    spark = SparkWrapper.get_spark()

    # A trivial round trip through Spark confirms the session actually
    # works, not just that it was constructed.
    df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "value"])
    assert df.count() == 2
    assert sorted(row["value"] for row in df.collect()) == ["a", "b"]
