"""End-to-end px-file builds using the Spark backend.

Run only inside Azure Databricks (a live Spark session is required), via::

    uv run pytest -m databricks tests/spark

These mirror the pandas-backend equivalents in tests/controll/, but build
with backend="spark" to exercise the Spark code path end-to-end against
the same fixture data.
"""

import pxbuild


def test_cube_1_spark_backend_dont_crash():
    model = pxbuild.build_px_file("1", "testdata/test_cube_1/test_config.json", backend="spark")

    assert model.statistics.output_files
    assert model.statistics.row_count > 0


def test_cube_2_spark_backend_matches_pandas_data():
    spark_model = pxbuild.build_px_file("2", "testdata/test_cube_2/test_config.json", backend="spark")
    pandas_model = pxbuild.build_px_file("2", "testdata/test_cube_2/test_config.json", backend="pandas")

    def data_section(path: str) -> list:
        with open(path, encoding="iso-8859-1") as fh:
            content = fh.read()
        return content.split("DATA=", 1)[1].rstrip().rstrip(";").split()

    assert data_section(spark_model.statistics.output_files[0]) == data_section(pandas_model.statistics.output_files[0])
