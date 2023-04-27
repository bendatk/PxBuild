﻿from pxtool.model.util._px_super import _PxSingle
from pxtool.model.util._px_valuetype import _PxStringList
from pxtool.model.util._line_validator import LineValidator

class _AttributeId(_PxSingle): 

    pxvalue_type:str = "_PxStringList"
    may_have_language:bool = False


    def set(self, attribute_id:list[str]) -> None:
        """ Not in normal use. See pdf """
        LineValidator.is_not_None( self._keyword, attribute_id)
        LineValidator.is_list_of_strings( self._keyword, attribute_id)
        my_value = _PxStringList(attribute_id)
        try:
            super().set(my_value)
        except Exception as e:
            msg = self._keyword + ":" +str(e)
            raise type(e)(msg) from e

    def get_value(self) -> list[str]:
        return super().get_value().get_value()
