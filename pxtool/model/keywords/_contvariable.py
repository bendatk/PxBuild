﻿from pxtool.model.util._px_super import _PxValueByKey
from pxtool.model.util._px_valuetype import _PxString
from pxtool.model.util._px_keytypes import _KeytypeLang
from pxtool.model.util._line_validator import LineValidator

class _Contvariable(_PxValueByKey): 

    pxvalue_type:str = "_PxString"
    may_have_language:bool = True
    _seen_languages={}

    def __init__(self) -> None:
        super().__init__("CONTVARIABLE")

    def set(self, contvariable:str, lang:str = None) -> None:
        """ which variable is the content variable """
        LineValidator.is_not_None( self._keyword, contvariable)
        LineValidator.is_string( self._keyword, contvariable)
        my_value = _PxString(contvariable)
        my_key = _KeytypeLang(lang)
        try:
            super().set(my_value,my_key)
        except Exception as e:
            msg = self._keyword + ":" +str(e)
            raise type(e)(msg) from e
        self._seen_languages[lang]=1

    def get_value(self, lang:str = None) -> str:
        my_key = _KeytypeLang(lang)
        return super().get_value(my_key).get_value()

    def has_value(self, lang:str = None) -> bool:
        my_key = _KeytypeLang(lang)
        return super().has_value(my_key)

    def get_used_languages(self) -> list[str]:
       return list(self._seen_languages.keys())

    def reset_language_none_to(self,lang:str)->None:
        if not lang:
            return
        if None in self.get_used_languages():
             super().reset_language_none_to(lang)
             #unsee None
             del self._seen_languages[None]
             self._seen_languages[lang]=1
