from pxbuild.control.load_from_pxfile import Loader
from pxbuild.operations_on_model.output.refine.fix_the_variable_type_keyword import fix_the_variable_type_keyword
import pytest
from tests._paths import data_path


def test_fix_the_variable_type_keyword_raises():
    dummy = Loader(data_path("px_files", "clean_me.px"))
    with pytest.raises(Exception, match="One of check_language, check_stub_and_heading, "):
        fix_the_variable_type_keyword(dummy.outModel)


def test_fix_the_variable_type_keyword_ok():
    dummy = Loader(data_path("px_files", "testdata2.px"))
    fix_the_variable_type_keyword(dummy.outModel)
    assert not dummy.outModel.variable_type.has_value("lala", "la")
