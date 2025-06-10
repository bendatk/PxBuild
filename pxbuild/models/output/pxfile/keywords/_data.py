from pxbuild.models.output.pxfile.util._px_super import _PxSingle
from pxbuild.models.output.pxfile.util._px_valuetype import _PxData
import pyspark.pandas as ps
import pandas as pd
from pyspark.sql import DataFrame as SparkDataFrame, Column as SparkColumn
from .....controll.helpers.datadata_helpers.pandas_spark_backend.pandas_spark_backend import PandasSparkBackend
from io import TextIOWrapper

class _Data(_PxSingle):

    pxvalue_type: str = "_PxData"
    has_subkey: bool = False
    subkey_optional: bool = False
    completeness_type: str = ""
    may_have_language: bool = False

    def __init__(self) -> None:
        super().__init__("DATA")

    def set(self, data: SparkDataFrame | pd.Series, columns_per_line: int) -> None:
        """Numbers and quoted dots"""
        my_value = _PxData(data, columns_per_line)
        try:
            super().set(my_value)
        except Exception as e:
            msg = self._keyword + ":" + str(e)
            raise type(e)(msg) from e
    
    def __str__(self):
        # Override parent method to add extra line feed before printing the actual data
        if self.has_value():
            return f"{self._keyword}=\n{self._px_value};"
        else:
            return ""

    def write_to_file(self, file_path, f: TextIOWrapper) -> None:
        if self.has_value() and isinstance(self._px_value, _PxData):
            f.write(f"{self._keyword}=\n")
            PandasSparkBackend.get_backend().write_pxdata_to_file(self._px_value, f, file_path, self._px_value._columns_per_line, chunk_size=500000)
            f.write(";")
        else:
            raise ValueError(f"Cannot write {self._keyword} without value.")
        
    def get_value(self):
        return super().get_value().get_value()

    def has_value(self) -> bool:
        return super().has_value()
