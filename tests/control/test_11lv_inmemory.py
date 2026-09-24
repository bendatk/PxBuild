"""End-to-end test building the 11lv (adoptions) px file fully in-memory."""

import pandas as pd
import pytest

import pxbuild
from pxbuild.models.output.pxfile.px_file_model import PXFileModel
from tests._paths import data_path, load_testdata_config

PXMETADATA_ID = "11lv"
DATASET_ENCODING = "utf-8-sig"


def _build_inmemory_config(output_dir) -> dict:
    config = load_testdata_config(data_path("real_world", "11lv", "config.json"), output_dir)
    dataframe = pd.read_parquet(data_path("real_world", "11lv", "11lv.parquet"))
    metadata_dict = config["admin"]["pxMetadataResource"]["adressFormat"]
    metadata_dict["dataset"]["dataFile"] = {PXMETADATA_ID: dataframe}

    config["admin"]["pxDataResource"] = {
        "resourceType": "dataframe",
        "adressFormat": "unused/{id}",
    }
    config["admin"]["skipCreationDate"] = True

    return config


@pytest.fixture()
def built_model(tmp_path) -> PXFileModel:
    config = _build_inmemory_config(tmp_path)

    model = pxbuild.build_px_file(PXMETADATA_ID, config, backend="pandas")

    assert model.statistics.output_files
    return model


def test_build_px_file_from_inmemory_dataframe_matches_expected_px_file(built_model: PXFileModel) -> None:
    output_file = built_model.statistics.output_files[0]

    with open(output_file, encoding=DATASET_ENCODING) as fh:
        actual_content = fh.read()

    with data_path("real_world", "11lv", "expected_11lv.px").open(encoding=DATASET_ENCODING) as fh:
        expected_content = fh.read()

    assert actual_content == expected_content
