from pxbuild.control.load_from_pxfile import Loader
from pxbuild.models.output.pxfile.px_file_model import PXFileModel
import pytest
from tests._paths import data_path


def _invalid_px_file(file_name: str) -> str:
    return str(data_path("validation", "px", file_name))


def _px_file(file_name: str) -> str:
    return str(data_path("px_files", file_name))


class TestBadStart:
    def test_badstart1_file_raises_value_error(self):
        with pytest.raises(ValueError, match="A PxFile must start with a letter"):
            Loader(_invalid_px_file("BadStart1.px"))

    def test_badstart2_file_raises_value_error(self):
        with pytest.raises(ValueError, match="A PxFile must start with a letter"):
            Loader(_invalid_px_file("BadStart2.px"))

    def test_badstart3_file_raises_value_error(self):
        with pytest.raises(ValueError, match="A PxFile must start with a letter"):
            Loader(_invalid_px_file("BadStart3.px"))


class TestQuoteUnquote:
    def test_quote_unquote1_file_raises_value_error(self):
        with pytest.raises(Exception, match="Hmm, there is something:wrongplacement1 between "):
            Loader(_invalid_px_file("QuoteUnquote1.px"))

    def test_quote_unquote2_file_raises_value_error(self):
        with pytest.raises(Exception, match="Hmm, expected non-empty UnquotedItem."):
            Loader(_invalid_px_file("QuoteUnquote2.px"))


class TestBadValues:
    def test_badvaluetype1_file_raises_value_error(self):
        with pytest.raises(
            Exception, match="Value for keypart AXIS-VERSION: Excepting single quoted string, but items has not len = 1"
        ):
            Loader(_invalid_px_file("BadValueType1.px"))

    def test_badvaluetype2_file_raises_value_error(self):
        with pytest.raises(
            Exception,
            match="Value for keypart AGGREGALLOWED: Excepting single unquoted string YES or NO, but items has not len = 1",
        ):
            Loader(_invalid_px_file("BadValueType2.px"))

    def test_badvaluetype3_file_raises_value_error(self):
        with pytest.raises(Exception, match="Value for keypart AGGREGALLOWED: Boolean values must be YES or NO, not"):
            Loader(_invalid_px_file("BadValueType3.px"))

    def test_badvaluetype4_file_raises_value_error(self):
        with pytest.raises(
            Exception,
            match="Value for keypart DECIMALS: Excepting an integer as single unquoted string, but items has not len = 1",
        ):
            Loader(_invalid_px_file("BadValueType4.px"))

    def test_badvaluetype5_file_raises_value_error(self):
        with pytest.raises(Exception, match="Value for keypart DECIMALS: integer value convertion"):
            Loader(_invalid_px_file("BadValueType5.px"))

    def test_badvaluetype6_file_raises_value_error(self):
        with pytest.raises(Exception, match="Bad list"):
            Loader(_invalid_px_file("BadValueType6.px"))

    def test_badvaluetype7_file_raises_value_error(self):
        with pytest.raises(Exception, match="Value for keypart LANGUAGES: List must start with quoted string"):
            Loader(_invalid_px_file("BadValueType7.px"))

    def test_badvaluetype8_file_raises_value_error(self):
        with pytest.raises(
            Exception, match="Value for keypart LANGUAGES: Bad list, at item-index1: expected comma found ."
        ):
            Loader(_invalid_px_file("BadValueType8.px"))


class TestValidFilesLoads:
    def test_statfin_khi_pxt_11xm_full_read_ok(self):
        dummy = Loader(_px_file("statfin_khi_pxt_11xm_full.px"))
        model: PXFileModel = dummy.outModel
        assert "MADE-WITH=" in model.unknown_keywords

    def test_ok_odd_usage_read_ok(self):
        Loader(_px_file("ok_odd_usage.px"))
