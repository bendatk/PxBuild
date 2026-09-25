import pytest


def pytest_collection_modifyitems(config, items):
    """Mark every test collected under tests/spark as 'databricks'.

    These tests exercise the Spark backend and require a real Spark
    session (a Databricks cluster in practice). They are written here so
    they exist and can be run inside an Azure Databricks job/notebook via
    ``uv run pytest -m databricks``, but the default local/CI test run
    (``uv run pytest``) excludes them via the ``addopts`` marker filter in
    pyproject.toml, so they are never executed on a laptop or in GitHub
    Actions.
    """
    marker = pytest.mark.databricks
    spark_dir = str(config.rootpath / "tests" / "spark")
    for item in items:
        if str(item.fspath).startswith(spark_dir):
            item.add_marker(marker)
