"""End-to-end px-file builds using the Spark backend.

Run only inside Azure Databricks (a live Spark session is required), via::

    uv run pytest -m databricks tests/spark

These mirror the pandas-backend equivalents in tests/control/, but build
with backend="spark" to exercise the Spark code path end-to-end against
the same fixture data.
"""

import csv
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, cast

import pxbuild
from pxbuild.control.helpers.datadata_helpers.pandas_spark_backend.spark_wrapper import (
    SparkWrapper,
)
from tests._paths import data_path, load_testdata_config


def _spark_output_path(tmp_path, name: str) -> Path:
    volume_path = os.environ.get("PXBUILD_SPARK_TEMP_VOLUME")
    if volume_path:
        return Path(volume_path) / f"pxbuild-output-{name}-{uuid.uuid4().hex}"
    return tmp_path / "spark"


def _build_spark_config(cube_id: str, tmp_path) -> dict:
    cube_path = data_path("cubes", f"cube_{cube_id}")
    config = load_testdata_config(cube_path / "test_config.json", _spark_output_path(tmp_path, f"cube-{cube_id}"))
    config["charset"] = "UTF-8"
    config["codePage"] = "utf-8"

    with (cube_path / f"pxmetadata_{cube_id}.json").open(encoding="utf-8-sig") as metadata_file:
        metadata = json.load(metadata_file)
    with (cube_path / "thedata.csv").open(encoding="utf-8-sig", newline="") as data_file:
        reader = csv.DictReader(data_file, delimiter=";")
        columns = reader.fieldnames
        if columns is None:
            raise ValueError(f"CSV fixture has no header: {data_file.name}")
        data = [tuple(row[column] for column in columns) for row in reader]

    dataframe = SparkWrapper.get_spark().createDataFrame(cast(Any, data), cast(Any, columns))
    metadata["dataset"]["dataFile"] = {cube_id: dataframe}
    config["admin"]["pxMetadataResource"] = {
        "resourceType": "dictionary",
        "adressFormat": metadata,
    }
    config["admin"]["pxDataResource"] = {
        "resourceType": "dataframe",
        "adressFormat": "unused/{id}",
    }
    return config


def _build_11lv_spark_config(tmp_path, parquet_path: Path) -> dict:
    fixture_path = data_path("real_world", "11lv")
    config = load_testdata_config(fixture_path / "config.json", _spark_output_path(tmp_path, "11lv"))
    dataframe = SparkWrapper.get_spark().read.parquet(str(parquet_path))
    config["admin"]["pxMetadataResource"]["adressFormat"]["dataset"]["dataFile"] = {"11lv": dataframe}
    config["admin"]["pxDataResource"] = {
        "resourceType": "dataframe",
        "adressFormat": "unused/{id}",
    }
    config["admin"]["skipCreationDate"] = True
    return config


def _stage_11lv_parquet() -> Path:
    volume_path = os.environ.get("PXBUILD_SPARK_TEMP_VOLUME")
    if not volume_path:
        raise RuntimeError("PXBUILD_SPARK_TEMP_VOLUME must be set for the 11lv Spark test")

    source = data_path("real_world", "11lv", "11lv.parquet")
    destination = Path(volume_path) / f"pxbuild-11lv-{uuid.uuid4().hex}.parquet"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination


def _data_section(path) -> list:
    with open(path, encoding="utf-8-sig") as file:
        content = file.read()
    return content.split("DATA=", 1)[1].rstrip().rstrip(";").split()


def _legacy_data_section(path) -> list:
    data = Path(path).read_bytes().split(b"DATA=", 1)[1].rstrip().rstrip(b";")
    return data.decode("utf-8").split()


def _save_mismatch_for_inspection(name: str, actual_content: str, expected_content: str) -> None:
    """Persist a failing comparison's actual/expected content in the shared volume for manual review."""
    volume_path = os.environ.get("PXBUILD_SPARK_TEMP_VOLUME")
    if not volume_path:
        return
    debug_dir = Path(volume_path) / f"pxbuild-debug-{name}-{uuid.uuid4().hex}"
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / f"actual_{name}.px").write_text(actual_content, encoding="utf-8-sig")
    (debug_dir / f"expected_{name}.px").write_text(expected_content, encoding="utf-8-sig")
    print(f"Mismatch saved for inspection at: {debug_dir}")


def test_cube_1_spark_backend_dont_crash(tmp_path):
    config = _build_spark_config("1", tmp_path)
    output_path = Path(config["admin"]["outputDestination"]["pxFolderFormat"])
    try:
        model = pxbuild.build_px_file("1", config, backend="spark")

        assert model.statistics.output_files
        assert model.statistics.row_count is not None and model.statistics.row_count > 0
    finally:
        shutil.rmtree(output_path, ignore_errors=True)


def test_cube_2_spark_backend_matches_expected_data(tmp_path):
    spark_config = _build_spark_config("2", tmp_path)
    output_path = Path(spark_config["admin"]["outputDestination"]["pxFolderFormat"])
    try:
        spark_model = pxbuild.build_px_file("2", spark_config, backend="spark")

        expected_file = data_path("cubes", "cube_2", "expected", "tab_2.px")

        try:
            assert _data_section(spark_model.statistics.output_files[0]) == _legacy_data_section(expected_file)
        except AssertionError:
            actual_content = Path(spark_model.statistics.output_files[0]).read_text(encoding="utf-8-sig")
            expected_content = expected_file.read_text(encoding="utf-8-sig")
            _save_mismatch_for_inspection("cube-2", actual_content, expected_content)
            raise
    finally:
        shutil.rmtree(output_path, ignore_errors=True)


def test_11lv_spark_backend_matches_expected_file(tmp_path):
    parquet_path = _stage_11lv_parquet()
    output_path = None
    try:
        config = _build_11lv_spark_config(tmp_path, parquet_path)
        output_path = Path(config["admin"]["outputDestination"]["pxFolderFormat"])
        model = pxbuild.build_px_file("11lv", config, backend="spark")

        expected_file = data_path("real_world", "11lv", "expected_11lv_spark.px")

        assert model.statistics.row_count == 9696
        actual_content = Path(model.statistics.output_files[0]).read_text(encoding="utf-8-sig")
        expected_content = expected_file.read_text(encoding="utf-8-sig")
        try:
            assert actual_content == expected_content
        except AssertionError:
            _save_mismatch_for_inspection("11lv", actual_content, expected_content)
            raise
    finally:
        parquet_path.unlink(missing_ok=True)
        if output_path is not None:
            shutil.rmtree(output_path, ignore_errors=True)
