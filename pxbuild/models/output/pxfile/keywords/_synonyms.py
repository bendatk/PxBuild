﻿from pxbuild.models.output.pxfile.util._px_super import _PxSingle
from pxbuild.models.output.pxfile.util._px_valuetype import _PxStringList
from pxbuild.models.output.pxfile.util._line_validator import LineValidator

class _Synonyms(_PxSingle): 

    pxvalue_type:str = "_PxStringList"
    has_subkey:bool = False
    subkey_optional:bool = False
    completeness_type:str = ""
    may_have_language:bool = False

    def __init__(self) -> None:
        super().__init__("SYNONYMS")

    def set(self, synonyms:list[str]) -> None:
        """ In use? """
        LineValidator.is_not_None( self._keyword, synonyms)
        LineValidator.is_list_of_strings( self._keyword, synonyms)
        my_value = _PxStringList(synonyms)
        try:
            super().set(my_value)
        except Exception as e:
            msg = self._keyword + ":" +str(e)
            raise type(e)(msg) from e

    def get_value(self) -> list[str]:
        return super().get_value().get_value()

    def has_value(self) -> bool:
        return super().has_value()

