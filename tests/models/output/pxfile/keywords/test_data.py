import pytest
from pxbuild.models.output.pxfile.keywords._data import _Data


def test_data_set_valid():
    obj = _Data()
    obj.set(["a string", "no"], 1)
    assert obj.get_value() == ["a string", "no"]


def test_data_has_value():
    obj = _Data()
    assert not obj.has_value()
    obj.set(["a string", "no"], 1)
    assert obj.has_value()


def test_data_str_empty_when_unset():
    obj = _Data()
    assert str(obj) == ""


def test_data_str_when_set():
    obj = _Data()
    obj.set(["a string", "no"], 1)
    assert str(obj).startswith("DATA=\n")


def test_data_duplicate_set_raises():
    obj = _Data()
    obj.set(["a string", "no"], 1)
    with pytest.raises(ValueError):
        obj.set(["a string", "no"], 1)
