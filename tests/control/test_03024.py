import pytest

import pxbuild
from pxbuild.models.output.pxfile.px_file_model import PXFileModel
from tests.testdata.reference import expected_03024 as expected


def _normalize(value: str) -> str:
    # Trailing ".0" on whole numbers is a formatting detail, not a data
    # difference, so it is ignored when comparing against the fixture.
    value = str(value)
    if value.endswith(".0"):
        value = value[:-2]
    return value


@pytest.fixture()
def out_model() -> PXFileModel:
    model = pxbuild.build_px_model("03024", "example_data/pxbuildconfig/ssb_config.json")
    return model.get_model("multi")


def test_03024_data(out_model: PXFileModel) -> None:
    actual_data = [_normalize(v) for v in out_model.data.get_value()]
    expected_data = [_normalize(v) for v in expected.DATA]

    assert actual_data == expected_data


def test_03024_decimals(out_model: PXFileModel) -> None:
    actual_decimals = out_model.decimals.get_value()

    assert actual_decimals == expected.DECIMALS
