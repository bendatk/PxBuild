﻿import pytest
from pxtool.models.output.pxfile.keywords._showdecimals import _Showdecimals
    
def test_Showdecimals_set_valid():
    obj = _Showdecimals()
    assert not obj.has_value()   
    obj.set(1)
    assert obj.has_value()    
    assert obj.get_value() == 1
    
def test_Showdecimals_duplicate_set_raises():
    obj = _Showdecimals()
    obj.set(1)
    with pytest.raises(Exception):
        obj.set(1)
