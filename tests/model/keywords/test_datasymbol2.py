﻿import pytest
from pxtool.model.keywords._datasymbol2 import _Datasymbol2
    
def test_Datasymbol2_set_valid():
    obj = _Datasymbol2()
    obj.set("a string","no")
    assert obj.get_value("no") == "a string"
    
def test_Datasymbol2_used_languages():
    obj = _Datasymbol2()
    obj.set("a string","no")
    assert "no" in obj.get_used_languages()

def test_Datasymbol2_reset_language():
    obj = _Datasymbol2()
    obj.set("a string",)
    assert None in obj.get_used_languages()
    obj.reset_language_none_to(None)    
    obj.reset_language_none_to("no")         
    assert not None in obj.get_used_languages()
    assert "no" in obj.get_used_languages()  

    
def test_Datasymbol2_duplicate_set_raises():
    obj = _Datasymbol2()
    obj.set("a string","no")
    with pytest.raises(Exception):
        obj.set("a string","no")