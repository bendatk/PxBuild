import pandas
from typing import List
from pxbuild.models.input.pydantic_pxbuildconfig import PxbuildConfig
from .parquet_datasource import ParquetDatasource
from .csv_datasource import CsvDatasource
from .spark_datasource import SparkDatasource
from .abstract_datasource import AbstractDatasource
from pxbuild.models.input.pydantic_pxmetadata import PxMetadata
from pxbuild.models.output.pxfile.util.commons import Commons
from ...helpers.logger_config import logger
from .pandas_spark_backend.pandas_spark_backend import PandasSparkBackend
from pyspark.sql import DataFrame as SparkDataFrame
from ....models.output.pxfile.util.commons import Commons
from pxbuild.models.input.pydantic_pxbuildconfig import ResourceType3

class PxDataSourceError(Exception):
    """Custom exception for errors related to datasource."""
    pass

class Datadatasource:
    def __init__(self, file_id: str, config: PxbuildConfig, pxmetadata: PxMetadata) -> None:
        data_file_path_format = config.admin.px_data_resource.adress_format
        data_file_resorce_type = config.admin.px_data_resource.resource_type
        self.measurements = pxmetadata.dataset.measurements

        if data_file_resorce_type == ResourceType3.file:
            self._data_file_path = data_file_path_format.format(id=file_id)
            if self._data_file_path.endswith(".parquet"):
                self._my_datasource: AbstractDatasource = ParquetDatasource(self._data_file_path)
            elif self._data_file_path.endswith(".csv"):
                self._my_datasource: AbstractDatasource = CsvDatasource(self._data_file_path)
            else:
                raise NotImplementedError("Sorry, not implemented yet. Files must end with .parquet or .csv")
        elif data_file_resorce_type == ResourceType3.dataframe and isinstance(pxmetadata.dataset.data_file, dict):
            dataframe = pxmetadata.dataset.data_file.get(file_id)
            self._data_file_path = "from_direct_reference"
            if dataframe is None:
                raise PxDataSourceError(f"No dataframe '{file_id}' found.")
            self._my_datasource: AbstractDatasource = SparkDatasource(dataframe)

        self._backend = PandasSparkBackend.get_backend()
        self._raw_df = self._my_datasource.get_raw_data()

        self._validate_data(self._raw_df, self._data_file_path)

    def _validate_data(self, df: pandas.DataFrame | SparkDataFrame, file_path: str) -> None:
        self._backend.validate_data(df, file_path)

    def validate_coded_values(self, column: str, codelist: List[str]) -> None:
        self._backend.validate_coded_values(self._raw_df, column, codelist)

    def get_timeperiodes(self, column_name: str) -> List[str]:
        return self._backend.get_timeperiodes(self._raw_df, column_name)

    def get_identifiercolumns(self, raw_data: pandas.DataFrame | SparkDataFrame, measurement_map: dict) -> List[str]:
        all_columns = self._backend.get_columns_to_list(raw_data)
        identifier_columns = []
        for column in all_columns:
            if not (column in measurement_map.keys()):
                identifier_columns.append(column)

        return identifier_columns

    def add_missing_symbolcolumns(self, measurement_codes: list[str], df: pandas.DataFrame | SparkDataFrame) -> SparkDataFrame | pandas.DataFrame:
        return self._backend.add_missing_symbolcolumns(measurement_codes, df)

    def make_renamedict(self, measurement_code_by_column_name: dict, columns_in_datafile) -> dict:
        my_out = {}
        for column_name in measurement_code_by_column_name:
            my_out[column_name] = f"VALUE_{measurement_code_by_column_name[column_name]}"
            corresponding_symbol_column = column_name + "_SYMBOL"
            if corresponding_symbol_column in columns_in_datafile:
                my_out[corresponding_symbol_column] = f"SYMBOL_{measurement_code_by_column_name[column_name]}"

        return my_out
    

    def round_by_decimals(self, df: pandas.DataFrame | SparkDataFrame) -> pandas.DataFrame | SparkDataFrame:
        return self._backend.round_by_decimals(df, self.measurements)


    def get_tidy_df(self, measure_dim_name: str, measurement_code_by_column_name: dict) -> pandas.DataFrame | SparkDataFrame:
        # measure_dim_name is contvariable_code from config
        # column_code_map is
        #        for measurement_var in self._pxmetadata_model.dataset.measurements:
        #           column_code_map[measurement_var.column_name] = measurement_var.code
        # aka measurement_codeBycolumn_name

        #  CODED_DIM1;CODED_DIM2;CODED_DIM3;TIME;MEASURE1;MEASURE2;MEASURE1_SYMBOL
        # using measurement_codeBycolumn_name
        #  rename all column_name to VALUE_{code}
        #  rename all {colname}_SYMBOL -> SYMBOL_{code}
        #  add missing SYMBOL_{code}
        #  it is when we do pd.wide_to_long, this strange mix of column names and code is needed: The code in the cell is the columnnane minus "VALUE"


        raw_data = self.round_by_decimals(self._my_datasource.get_raw_data())

        logger.debug(f"raw_data.columns: {raw_data.columns}")

        measurement_codes = list(measurement_code_by_column_name.values())
        column_with_value_prefix = self.make_renamedict(measurement_code_by_column_name, raw_data.columns)

        # todo attributes columns should not be counted as identifier_columns
        identifier_columns = self.get_identifiercolumns(raw_data, column_with_value_prefix)
        logger.debug(f"Renaming: {column_with_value_prefix}")
        raw_data = self._backend.rename(raw_data, column_with_value_prefix)
        logger.debug(f"Post renaming: {raw_data.columns}")
        raw_data = self.add_missing_symbolcolumns(measurement_codes, raw_data)
        logger.debug(f"Cols before wide_to_long: {raw_data.columns}")
        tidy_df = self._backend.wide_to_long(
            raw_data,
            identifier_columns,
            stubnames=["VALUE", "SYMBOL"],
            measurement_codes=measurement_codes,
            j_column_name=measure_dim_name,
            sep="_",
            suffix=f"(!?{'|'.join(measurement_codes)})",
        )
        #logger.debug(f"Cols after wide_to_long: {tidy_df.columns}")

        return tidy_df
