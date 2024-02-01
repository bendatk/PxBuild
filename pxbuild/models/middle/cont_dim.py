from typing import Dict, List
from .abstract_dim import AbstractDim
from pxbuild.controll.helpers.loaded_jsons import LoadedJsons
from pxbuild.controll.helpers.datadata_helpers.for_get_data import ForGetData


class ContDim(AbstractDim):
    def __init__(self, inLoadedJsons: LoadedJsons) -> None:
        meta = inLoadedJsons.get_pxmetadata().dataset
        config = inLoadedJsons.get_config()
        super().__init__(config.contvariable_code, config.contvariable)

        if not meta.measurements:
            raise Exception("Sorry, dataset is missing measurment.")

        languages = config.admin.valid_languages

        self._codes: List[str] = []
        self._labels_by_lang: Dict[str, List[str]] = {}
        self._labels_by_code: Dict[str, Dict[str, str]] = {}

        for lang in languages:
            self._labels_by_lang[lang] = []

        for my_cont in meta.measurements:
            my_cont_code = my_cont.code if my_cont.code is not None else my_cont.column_name
            self._codes.append(my_cont_code)
            self._labels_by_code[my_cont_code] = my_cont.label
            for lang in languages:
                self._labels_by_lang[lang].append(my_cont.label[lang])

        self._for_get_data = ForGetData(config.contvariable_code, self._codes)

    def get_codes(self) -> List[str]:
        return self._codes

    def get_labels(self, language: str) -> List[str]:
        return self._labels_by_lang[language]

    def get_valuelabel(self, language: str, value_code: str) -> str:
        return self._labels_by_code[value_code][language]

    def get_ForGetData(self, language: str) -> ForGetData:
        return self._for_get_data

    def get_variabletype(self) -> str:
        return "C"