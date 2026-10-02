# from .pydantic_pxcodes import PxCodes, Grouping, Valueitem, Note

from pxbuild.control.helpers.datadata_helpers.datadatasource import Datadatasource
from pxbuild.control.helpers.loaded_jsons import LoadedJsons
from pxbuild.models.input.helper_pxcodes import HelperPxCodes

from .abstract_dim import AbstractDim
from .coded_dim import CodedDim
from .cont_dim import ContDim
from .time_dim import TimeDim


class Dims:
    def __init__(self, in_loaded_jsons: LoadedJsons, in_datadatasource: Datadatasource) -> None:

        meta = in_loaded_jsons.get_pxmetadata().dataset

        self.dim_by_code: dict[str, AbstractDim] = {}
        self._stubCodes: list[str] = []
        self._headingCodes: list[str] = []

        self.coded_dimensions: list[CodedDim] = []

        # CodedDimensions
        if meta.coded_dimensions:
            # In input 2 CodedDimensions can share a codelist. This cannot be expressed in output.
            pxcodes_by_codelist_id = in_loaded_jsons.get_resolved_pxcodes_ids()
            pxcodes_helper_by_codelist_id: dict[str, HelperPxCodes] = {}
            for codelist_id in pxcodes_by_codelist_id:
                pxcodes_helper_by_codelist_id[codelist_id] = HelperPxCodes(
                    pxcodes_by_codelist_id[codelist_id], in_loaded_jsons.get_config().admin.valid_languages
                )

            for n_dim in meta.coded_dimensions:
                temp_cd = CodedDim(n_dim, pxcodes_helper_by_codelist_id[n_dim.codelist_id], in_loaded_jsons)
                n_code = temp_cd.get_code()
                # Defaults to stub as is_heading is optional property without default value
                if n_dim.is_heading:
                    self._headingCodes.append(n_code)
                else:
                    self._stubCodes.append(n_code)
                self.dim_by_code[n_code] = temp_cd
                self.coded_dimensions.append(temp_cd)

        # CONT
        self.contdim: ContDim = ContDim(in_loaded_jsons)
        contdim_code = self.contdim.get_code()
        if meta.is_heading_contdim or meta.is_heading_contdim is None:
            self._headingCodes.append(contdim_code)
        else:
            self._stubCodes.append(contdim_code)
        self.dim_by_code[contdim_code] = self.contdim

        # TIME
        if meta.time_dimension.codelist_id:
            pxcodes_time = in_loaded_jsons.get_resolved_pxcodes_ids().get(meta.time_dimension.codelist_id, None)
        else:
            pxcodes_time = None
        self.time: TimeDim = TimeDim(in_loaded_jsons, in_datadatasource, pxcodes_time)
        time_code = self.time.get_code()
        # Defaults to heading as is_heading is optional property without default value
        if meta.time_dimension.is_heading:
            self._headingCodes.append(time_code)
        else:
            self._stubCodes.append(time_code)
        self.dim_by_code[time_code] = self.time

    def get_dims_in_output_order(self) -> list[AbstractDim]:
        my_out: list[AbstractDim] = []
        for code in self._stubCodes + self._headingCodes:
            my_out.append(self.dim_by_code[code])
        return my_out

    def get_stubcodes(self) -> list[str]:
        return self._stubCodes

    def get_headingcodes(self) -> list[str]:
        return self._headingCodes

    def get_dimcodes_in_output_order(self) -> list[str]:
        return self._stubCodes + self._headingCodes

    def get_as_lables(self, codes: list[str], language: str) -> list[str]:
        my_out: list[str] = []
        for code in codes:
            my_out.append(self.dim_by_code[code].label_by_lang[language])
        return my_out
