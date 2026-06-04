from pxbuild.models.input.pydantic_pxcodes import PxCodes

from .abstract_dim import AbstractDim
from ..input.pydantic_pxmetadata import Note
from typing import List
from pxbuild.controll.helpers.datadata_helpers.datadatasource import Datadatasource
from pxbuild.controll.helpers.loaded_jsons import LoadedJsons


from pxbuild.controll.helpers.datadata_helpers.for_get_data import CubemathsHelper


class TimeDim(AbstractDim):
    def __init__(self, in_loaded_jsons: LoadedJsons, in_datadatasource: Datadatasource, in_pxcodes: PxCodes | None) -> None:
        meta = in_loaded_jsons.get_pxmetadata().dataset
        config = in_loaded_jsons.get_config()
        super().__init__(config.timevariable_code, meta.time_dimension.label)

        col_name = meta.time_dimension.column_name

        self._periods = in_datadatasource.get_timeperiodes(col_name)
        self._period_labels = {
            lang: self._periods 
            for lang in config.admin.valid_languages
        }
        self._period_codes =  [str(period).replace('*', '') for period in self._periods]
        
        if in_pxcodes:
            labels_by_lang_and_code = {
                lang: {
                    str(v.code): ((v.label or {}).get(lang) or str(v.code))
                    for v in in_pxcodes.valueitems
                    if v.code is not None
                }
                for lang in config.admin.valid_languages
            }
            self._period_labels = {
                lang: [labels_by_lang_and_code[lang].get(code, code) for code in self._period_codes]
                for lang in config.admin.valid_languages
            }  
        
        
        
        self._variable_type = config.timevariable_type
        self._for_get_data = CubemathsHelper(col_name, self._periods)
        self._value_notes = meta.time_dimension.value_notes
        self._notes = meta.time_dimension.notes

    # for time : code == label

    def get_codes(self) -> List[str]:
        return self._period_codes

    def get_labels(self, language: str) -> List[str]:
        return self._period_labels.get(language, [])


    def get_valuelabel(self, language: str, value_code: str) -> str:
        labels = self._period_labels.get(language, [])
        if value_code in self._period_codes:
            return labels[self._period_codes.index(value_code)]
        return value_code

    def get_cubemaths_helper(self, language: str) -> CubemathsHelper:
        return self._for_get_data

    def get_variabletype(self) -> str:
        return "T" if self._variable_type is None else self._variable_type




