﻿import pytest
from pxtool.model.keywords._notex import _Notex
    
def test_Notex_set_valid():
    obj = _Notex()
    obj.set("a string","region","no")
    assert obj.get_value("region","no") == "a string"
    
def test_Notex_used_languages():
    obj = _Notex()
    obj.set("a string","region","no")
    assert "no" in obj.get_used_languages()

def test_Notex_reset_language():
    obj = _Notex()
    obj.set("a string","region")
    assert None in obj.get_used_languages()
    obj.reset_language_none_to(None)    
    obj.reset_language_none_to("no")         
    assert not None in obj.get_used_languages()
    assert "no" in obj.get_used_languages()  

    
def test_Notex_hack_multi_duplicate_set_raises():
    obj = _Notex()
    obj.set("a string","region","no")
    #reseting counter to create error
    obj.occurence_counter=0
    with pytest.raises(Exception) as err_mess:
        obj.set("a string","region","no")
    assert str(err_mess.value).startswith("NOTEX:")