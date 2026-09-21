"""End-to-end test building the 11lv (adoptions) px file fully in-memory.

Unlike test_11lv_keywords.py (which points the config at the parquet file on
disk), this test reads the parquet fixture into a pandas DataFrame itself and
feeds it into pxbuild through the "dataframe" resource type, i.e. the same
in-memory style an end user would use when they already hold the data (and
metadata) as Python objects instead of files on disk.

The test passes if the generated .px file matches a pre-generated golden
file (testdata/test_11lv/expected_11lv.px) byte-for-byte. CREATION-DATE is
skipped (skipCreationDate=True) so the output is fully deterministic.
"""

import copy
import json
import os

import pandas as pd
import pytest

import pxbuild
from pxbuild.models.output.pxfile.px_file_model import PXFileModel

CONFIG_PATH = "testdata/test_11lv/config.json"
DATA_PATH = "testdata/test_11lv/11lv.parquet"
EXPECTED_PATH = "testdata/test_11lv/expected_11lv.px"
OUTPUT_FOLDER = "testdata/out_files/test_11lv_inmemory/"
PXMETADATA_ID = "11lv"
DATASET_ENCODING = "utf-8-sig"


def _build_inmemory_config() -> dict:
    """Load config.json and rewire it for the fully in-memory build.

    - The data resource becomes "dataframe" instead of "file": the actual
      data is supplied as a {file_id: DataFrame} dict on the (already
      in-memory) pxmetadata dict, rather than pxbuild reading a parquet
      file itself.
    - skipCreationDate is turned on so the output is reproducible.
    - Output is redirected to its own folder so this test never collides
      with the file-based test_11lv_keywords.py fixtures/output.
    """
    with open(CONFIG_PATH, encoding="utf-8-sig") as fh:
        config = json.load(fh)
    config = copy.deepcopy(config)

    dataframe = pd.read_parquet(DATA_PATH)
    metadata_dict = config["admin"]["pxMetadataResource"]["adressFormat"]
    metadata_dict["dataset"]["dataFile"] = {PXMETADATA_ID: dataframe}

    config["admin"]["pxDataResource"] = {
        "resourceType": "dataframe",
        "adressFormat": "unused/{id}",
    }
    config["admin"]["skipCreationDate"] = True
    config["admin"]["outputDestination"] = {
        "resourceType": "folders",
        "pxFolderFormat": OUTPUT_FOLDER,
        "aggFolderFormat": OUTPUT_FOLDER,
    }

    return config


@pytest.fixture()
def built_model() -> PXFileModel:
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    config = _build_inmemory_config()

    model = pxbuild.build_px_file(PXMETADATA_ID, config, backend="pandas")

    assert model.statistics.output_files
    return model


def test_build_px_file_from_inmemory_dataframe_matches_expected_px_file(built_model: PXFileModel) -> None:
    output_file = built_model.statistics.output_files[0]

    with open(output_file, encoding=DATASET_ENCODING) as fh:
        actual_content = fh.read()

    with open(EXPECTED_PATH, encoding=DATASET_ENCODING) as fh:
        expected_content = fh.read()

    assert actual_content == expected_content
