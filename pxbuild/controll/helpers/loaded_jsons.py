import json

from typing import Dict

from pxbuild.models.input.pydantic_pxbuildconfig import PxbuildConfig
from pxbuild.models.input.pydantic_pxmetadata import PxMetadata
from pxbuild.models.input.pydantic_pxstatistics import PxStatistics
from pxbuild.models.input.pydantic_pxcodes import PxCodes
from ..helpers.logger_config import logger
from pxbuild.models.input.pydantic_pxbuildconfig import ResourceType, ResourceType1

# Class for loading all jsons into pydantic. And nothing else.
class LoadedJsons:
    """
    Class for loading all jsons into pydantic. And nothing else.
    """

    def __init__(self, pxmetadata_id: str, config_file: str | dict) -> None:
        self._pxmetadata_id = pxmetadata_id
        self._config = LoadedJsons.load_config(config_file)

        pxmetadata_format = self._config.admin.px_metadata_resource.adress_format
        pxmetadata_source_type = self._config.admin.px_metadata_resource.resource_type
        if isinstance(pxmetadata_format, str) and pxmetadata_source_type == ResourceType.file:
            # pxmetadataFormat="example_data/pxmetadata/{id}.json"
            pxmetadata_file = pxmetadata_format.format(id=self._pxmetadata_id)
            with open(pxmetadata_file, encoding="utf-8-sig") as f:
                pxmetadata_input = json.loads(f.read())
        elif isinstance(pxmetadata_format, dict) and pxmetadata_source_type == ResourceType.dictionary:
            pxmetadata_input = pxmetadata_format
        self._pxmetadata_model = PxMetadata(**pxmetadata_input)

        
        pxstatistics_format = self._config.admin.px_statistics_resource.adress_format
        pxstatistics_source_type = self._config.admin.px_statistics_resource.resource_type
        if isinstance(pxstatistics_format, str) and pxstatistics_source_type == ResourceType1.file:
            # pxstatisticsFormat="example_data/pxstatistics/pxstatistics_{id}.json"
            pxstatistics_file = pxstatistics_format.format(id=self._pxmetadata_model.dataset.statistics_id)
            with open(pxstatistics_file, encoding="utf-8-sig") as f:
                pxstatistics_input = json.loads(f.read())
        elif isinstance(pxstatistics_format, dict) and pxstatistics_source_type == ResourceType1.dictionary:
            pxstatistics_input = pxstatistics_format
        self._pxstatistics = PxStatistics(**pxstatistics_input)


        self._resolved_pxcodes_ids: Dict[str, PxCodes] = {}
        if self._pxmetadata_model.dataset.coded_dimensions:

            # pxcodesFormat="example_data/pxcodes/{id}.json"
            pxcodes_format = self._config.admin.px_codes_resource.adress_format
            pxcodes_source_type = self._config.admin.px_codes_resource.resource_type
            for dimension in self._pxmetadata_model.dataset.coded_dimensions:

                if dimension.codelist_id not in self._resolved_pxcodes_ids:
                    if isinstance(pxcodes_format, str) and pxcodes_source_type == ResourceType1.file:
                        tmp_path = pxcodes_format.format(id=dimension.codelist_id)
                        with open(tmp_path, encoding="utf-8-sig") as f:
                            json1 = json.loads(f.read())
                    elif isinstance(pxcodes_format, dict) and pxcodes_source_type == ResourceType1.dictionary:
                        json1 = pxcodes_format.get(dimension.codelist_id, {})

                    self._resolved_pxcodes_ids[dimension.codelist_id] = PxCodes(**json1)

    def get_config(self) -> PxbuildConfig:
        return self._config

    def get_pxmetadata(self) -> PxMetadata:
        return self._pxmetadata_model

    def get_pxstatistics(self) -> PxStatistics:
        return self._pxstatistics

    def get_resolved_pxcodes_ids(self) -> Dict[str, PxCodes]:
        """
        PxCodes as a function of codelist_id.

        Parameters:
        a (int): The first number to add.
        b (int): The second number to add.

        Returns: Empty if the dataset has no coded_dimensions
        """
        return self._resolved_pxcodes_ids

    @staticmethod
    def load_config(config_file: str | dict) -> PxbuildConfig:
        if isinstance(config_file, str):
            with open(config_file, encoding="utf-8-sig") as f:
                config = json.loads(f.read())
        elif isinstance(config_file, dict):
            config = config_file
        return PxbuildConfig(**config)
