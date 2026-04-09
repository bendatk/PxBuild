import pandas as pd
from typing import Literal, List
from pyarrow.parquet import ParquetFile
import numpy as np
from .....models.output.pxfile.keywords._data import _PxData
from io import TextIOWrapper
from .....models.output.pxfile.util.commons import Commons
from .....models.input.pydantic_pxmetadata import Measurement
from ._backend_methods import IBackendMethods


class PandasWrapper(IBackendMethods):

    @property
    def backend_name(self) -> str:
        return "pandas"

    def add_out_index(self, df: pd.DataFrame, cubemaths_helper_by_codeid: dict) -> pd.DataFrame:
        columns_to_sum = []
        for col in cubemaths_helper_by_codeid.values():
            # Mapping the values using the dictionary
            contrib_col_name = "int_" + col._colname_in_dataframe
            df[contrib_col_name] = df[col._colname_in_dataframe].map(col._position_of_value) * col.factor
            columns_to_sum.append(contrib_col_name)
        return self.add_sum_column(df, "out_index", columns_to_sum)

    def get_columns_to_list(self, df: pd.DataFrame) -> List[str]:
        return df.columns.values.tolist()

    def rename(self, df: pd.DataFrame, measurement_code_by_column_name: dict) -> pd.DataFrame:
        return df.rename(columns=measurement_code_by_column_name)

    def round_by_decimals(self, df: pd.DataFrame, measurements: List[Measurement]) -> pd.DataFrame:
        for my_cont in measurements:
            df[my_cont.column_name] = df[my_cont.column_name].round(Commons.get_decimals())
        return df

    def get_timeperiodes(self, df: pd.DataFrame, column_name: str) -> List[str]:
        """Reads all values from a column, applies unique and sorts descending."""

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in the CSV file.")

        column_data = df[column_name]

        # Get distinct values from the column
        distinct_values = column_data.unique()
        as_list = distinct_values.tolist()
        as_sorted_list = sorted(as_list)
        return as_sorted_list

    def validate_coded_values(self, df: pd.DataFrame, column: str, codelist: List[str]) -> None:
        """Validates that all values in a column are in a list of valid values."""

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in the data.")

        column_data = df[column]

        # Create a mask for invalid entries (not in valid_values and not NaN)
        mask = ~column_data.isin(codelist) & column_data.notna()

        # Filter the DataFrame with the mask
        invalid_rows = df[mask]
        if not invalid_rows.empty:
            err_mess = f"There are rows with invalid values in column '{column}'."
            raise ValueError(err_mess)

    def wide_to_long(self, df: pd.DataFrame, identifier_cols: list[str], stubnames: list[str], measurement_codes: list[str], j_column_name: str, sep: str, suffix: str) -> pd.DataFrame:
        return pd.wide_to_long(
            df, stubnames=stubnames, i=identifier_cols, j=j_column_name, sep=sep, suffix=suffix
        ).reset_index()

    def read_parquet(self, parquet: ParquetFile) -> pd.DataFrame:
        return parquet.read().to_pandas()
    
    def read_csv(self, filepath) -> pd.DataFrame:
        return pd.read_csv(filepath, sep=";", dtype=str)
    
    def add_sum_column(self, df: pd.DataFrame, sum_col_name: str, columns: list[str]) -> pd.DataFrame:
        df[sum_col_name] = df[columns].sum(axis=1)
        return df

    def merge(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        on: str,
        how: Literal["left", "right", "outer", "inner", "cross"] = "left"
    ) -> pd.DataFrame:
        return pd.merge(df1, df2, on=on, how=how)

    def write_pxdata_to_file(self, data: _PxData, filepath: str, file_path: str, columns_per_line, chunk_size) -> None:
        pass

    def validate_data(self, df: pd.DataFrame, data_file_path: str) -> None:
        valid_symbol_entries = ["", ".", "..", "...", "....", ".....", "......", "-"]
        err_mess_ending = " From datafile " + data_file_path
        my_colnames: List[str] = df.columns.to_list()

        for col in my_colnames:
            if "." in col:
                raise ValueError(
                    "Column: "
                    + col
                    + " has a dot, if it is not so in the datafile, there probably is a duplicate in columnname. "
                    + err_mess_ending
                )

            if col.endswith("_SYMBOL"):
                col_without_symbol = col[:-7]
                if col_without_symbol not in my_colnames:
                    raise ValueError(
                        "Found " + col + " ,but no matching " + col_without_symbol + " . " + err_mess_ending
                    )

                # Create a mask for invalid entries (not in valid_symbol_entries and not NaN)
                mask = ~df[col].isin(valid_symbol_entries) & df[col].notna()

                # Filter the DataFrame with the mask
                invalid_rows = df[mask]
                if not invalid_rows.empty:
                    err_mess = "There are rows with bad value in " + col + " column. " + err_mess_ending
                    print(invalid_rows.head(10))
                    raise ValueError(err_mess)

    def add_missing_symbolcolumns(self, measurement_codes: list[str], df: pd.DataFrame) -> pd.DataFrame:
        for code in measurement_codes:
            if f"SYMBOL_{code}" not in df.columns:
                df[f"SYMBOL_{code}"] = ""
        return df

    def add_out_value(self, df: pd.DataFrame, missing_cell_symbol: str) -> pd.DataFrame:
        conditions = [df["SYMBOL"].notna() & (df["SYMBOL"] != ""), df["VALUE"].notna() & (df["VALUE"] != "")]

        choices = [df["SYMBOL"].astype(str), df["VALUE"].astype(str)]

        df["out_value"] = np.select(conditions, choices, missing_cell_symbol)
        return df
    
    def add_missing_rows(self, matrix_size, missing_row_symbol, df: pd.DataFrame) -> pd.DataFrame:
        # sorts on index as sideeffect :-)
        matrix_df = pd.DataFrame({"out_index": range(matrix_size)})
        merged_df = self.merge(matrix_df, df, on="out_index", how="left")

        # Fill missing values with "MISSING"
        merged_df["out_value"] = merged_df["out_value"].fillna(missing_row_symbol)
        return merged_df
    
    def remove_trailing_zero_decimals(self, df: pd.DataFrame) -> pd.Series:
        out_data = df["out_value"]
        mask = (
            out_data.astype(str).str.replace('.', '', 1).str.isdigit() &
            out_data.astype(str).str.contains('.', regex=False)
        )
        return out_data.where(~mask, out_data.astype(str).str.rstrip('0').str.rstrip('.'))

    def validate_codelist_vs_data_values(self, df: pd.DataFrame, coded_dimensions: list, resolved_pxcodes_ids: dict) -> None:
        for coded_dim in coded_dimensions:
            dim_code = coded_dim.code
            dim_column_name = coded_dim.column_name
            dim_values = df[dim_column_name].unique()
            codelist_values = [item.code for item in resolved_pxcodes_ids[coded_dim.codelist_id].valueitems]
            missing_values = [value for value in dim_values.tolist() if value not in codelist_values]
            if missing_values:
                raise ValueError(
                    'Values {} in dataset for coded dimension "{}" are not in codelist "{}".'.format(
                        ', '.join(f'"{x}"' for x in list(missing_values)), dim_code, coded_dim.codelist_id
                    )
                )
