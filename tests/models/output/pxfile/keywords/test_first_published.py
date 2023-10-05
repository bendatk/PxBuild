﻿import pytest
from pxtool.models.output.pxfile.keywords._first_published import _FirstPublished
    
def test_FirstPublished_set_valid():
    obj = _FirstPublished()
    assert not obj.has_value()   
    obj.set("a string")
    assert obj.has_value()    
    assert obj.get_value() == "a string"
    
def test_FirstPublished_duplicate_set_raises():
    obj = _FirstPublished()
    obj.set("a string")
    with pytest.raises(Exception):
        obj.set("a string")