import types
from typing import cast

import pytest

from pxbuild.control.helpers.datadata_helpers.datadatasource import Datadatasource
from pxbuild.control.helpers.datadata_helpers.pandas_spark_backend.pandas_spark_backend import (
    create_backend,
)
from pxbuild.control.helpers.loaded_jsons import LoadedJsons
from pxbuild.models.input.pydantic_pxmetadata import PxMetadata
from tests._paths import data_path

_FAKE_PXMETADATA = cast(PxMetadata, types.SimpleNamespace(dataset=types.SimpleNamespace(measurements=[])))
_BACKEND = create_backend("pandas")
_CONFIG_FILE = str(data_path("validation", "csv", "test_config.json"))


class TestDatadataValidation:
    def test_duplicate_column_name_raises(self):
        with pytest.raises(ValueError):
            Datadatasource(
                "duplicate_column_name.csv",
                LoadedJsons.load_config(_CONFIG_FILE),
                _FAKE_PXMETADATA,
                _BACKEND,
            )

    def test_has_status_column_but_no_measure_column_raises(self):
        with pytest.raises(ValueError):
            Datadatasource(
                "has_status_column_but_no_measure_column.csv",
                LoadedJsons.load_config(_CONFIG_FILE),
                _FAKE_PXMETADATA,
                _BACKEND,
            )

    def test_bad_value_in_status_column_raises(self):
        with pytest.raises(ValueError):
            Datadatasource(
                "bad_value_in_status_column.csv",
                LoadedJsons.load_config(_CONFIG_FILE),
                _FAKE_PXMETADATA,
                _BACKEND,
            )
