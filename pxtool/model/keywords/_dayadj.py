﻿from pxtool.model.util._px_super import _PxValueByKey
from pxtool.model.util._px_valuetype import _PxBool
from pxtool.model.util._px_keytypes import _KeytypeContentLang
from pxtool.model.util._line_validator import LineValidator

class _Dayadj(_PxValueByKey): 

    pxvalue_type:str = "_PxBool"
    may_have_language:bool = True
    _seen_languages={}


    def set(self, dayadj:bool, content:str=None, lang:str = None) -> None:
        """ data is adjusted e.g. to take into account the number of working days """
        LineValidator.is_not_None( self._keyword, dayadj)
        LineValidator.is_bool( self._keyword, dayadj)
        my_value = _PxBool(dayadj)
        my_key = _KeytypeContentLang(content, lang)
        try:
            super().set(my_value,my_key)
        except Exception as e:
            msg = self._keyword + ":" +str(e)
            raise type(e)(msg) from e
        self._seen_languages[lang]=1

    def get_value(self, my_key: _KeytypeContentLang) -> _PxBool:
        return super().get_value(my_key)

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