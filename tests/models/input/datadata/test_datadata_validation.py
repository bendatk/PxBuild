import types

import pytest
from pxbuild.controll.helpers.datadata_helpers.datadatasource import Datadatasource
from pxbuild.controll.helpers.datadata_helpers.pandas_spark_backend.pandas_spark_backend import create_backend
from pxbuild.controll.helpers.loaded_jsons import LoadedJsons

# These tests exercise Datadatasource's raw-data validation directly, so a
# minimal stand-in for PxMetadata (only .dataset.measurements is read before
# validation runs) is enough; a full PxMetadata isn't needed.
_FAKE_PXMETADATA = types.SimpleNamespace(dataset=types.SimpleNamespace(measurements=[]))


class TestDatadataValidation:
    def _config(self):
        return LoadedJsons.load_config("testdata/BadData/test_config.json")

    def test_duplicate_column_name_raises(self):
        with pytest.raises(ValueError):
            Datadatasource("duplicate_column_name.csv", self._config(), _FAKE_PXMETADATA, create_backend("pandas"))

    def test_has_status_column_but_no_measure_column_raises(self):
        with pytest.raises(ValueError):
            Datadatasource(
                "has_status_column_but_no_measure_column.csv",
                self._config(),
                _FAKE_PXMETADATA,
                create_backend("pandas"),
            )

    def test_bad_value_in_status_column_raises(self):
        with pytest.raises(ValueError):
            Datadatasource("bad_value_in_status_column.csv", self._config(), _FAKE_PXMETADATA, create_backend("pandas"))
