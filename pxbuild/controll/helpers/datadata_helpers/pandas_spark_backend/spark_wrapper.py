from typing import Literal, List, TYPE_CHECKING
from pyarrow.parquet import ParquetFile
from io import BufferedWriter
from functools import reduce
from .....models.output.pxfile.keywords._data import _PxData
from .....models.input.pydantic_pxmetadata import Measurement
from ._backend_methods import IBackendMethods
from pxbuild.models.output.pxfile.util.commons import Commons

import operator
import shutil
import glob
import os
import contextlib
import io

if TYPE_CHECKING:
    from pyspark.sql import SparkSession, DataFrame as SparkDataFrame

class SparkWrapper(IBackendMethods):

    def _init_(self) -> None:
        import importlib.util
        if importlib.util.find_spec("pyspark.sql") is None:
            raise ImportError("SparkWrapper requires a Spark environment with pyspark available.")

    @property
    def backend_name(self) -> str:
        return "spark"
    
    @staticmethod
    def get_spark() -> "SparkSession":
        try:
            from databricks.connect import DatabricksSession
            return DatabricksSession.builder.getOrCreate()
        except ImportError:
            from pyspark.sql import SparkSession
            return SparkSession.builder.getOrCreate() # type: ignore
        
    SPARKDATAFRAMETYPES = [
        "<class 'pyspark.sql.dataframe.DataFrame'>", 
        "<class 'pyspark.sql.connect.dataframe.DataFrame'>",
        "<class 'pyspark.sql.classic.dataframe.DataFrame'>"
    ]

    # 
    # File I/O methods
    #
    def write_pxdata_to_file(
        self,
        data: _PxData, 
        output_handle: BufferedWriter, 
        temp_volume_base_path: str, 
        columns_per_line: int
    ):
        from pyspark.sql import functions as F

        df = data._data.select("out_index", "out_value")

        line_idx = (F.col("out_index") / columns_per_line).cast("long")
        df_grouped = (
            df
            .withColumn("line_idx", line_idx)
            .groupBy("line_idx")
            .agg(
                F.concat_ws(
                    " ",
                    F.expr(
                        "transform("
                        "   sort_array(collect_list(struct(out_index, out_value))), "
                        "   x -> x.out_value"
                        ")"
                    ),
                ).alias("out_concat")
            )
            .withColumn("out_concat", F.concat(F.col("out_concat"), F.lit(" ")))
        )
    
        # todo: this is quite a arbitrary way to set the number of partitions - memory should be taken into account also
        # num_partitions = None
        # if Commons.get_matrix_size():
        #     def get_num_workers(spark):
        #         try:
        #             return int(spark.conf.get("spark.databricks.clusterUsageTags.clusterMaxWorkers", 1))
        #         except Exception:
        #             return int(spark.conf.get("spark.executor.instances", "1"))
        #     num_workers = get_num_workers(self.get_spark())
        #     num_partitions = max(4 * num_workers, int(Commons.get_matrix_size() / 5000000)+1)

        # if num_partitions:
        #     df_grouped = df_grouped.repartitionByRange(num_partitions, "line_idx")
        # else:
        #     df_grouped = df_grouped.repartitionByRange("line_idx")

        df_sorted = (
                df_grouped
                .repartitionByRange("line_idx")
                .sortWithinPartitions("line_idx")
                .select("out_concat")
            )
        
        df_sorted.write.mode("overwrite").text(temp_volume_base_path)

        part_files = sorted(glob.glob(os.path.join(temp_volume_base_path, "part-*.txt")))

        def get_dbutils(spark):
            try:
                from pyspark.dbutils import DBUtils
                dbutils = DBUtils(spark)
            except ImportError:
                import IPython
                dbutils = IPython.get_ipython().user_ns["dbutils"] # type: ignore
            return dbutils

        dbutils = get_dbutils(self.get_spark())

        if part_files:
            last_part = part_files[-1]
            with open(last_part, 'rb+') as f:
                f.seek(0, os.SEEK_END)
                end_pos = f.tell()
                while end_pos > 0:
                    f.seek(end_pos - 1)
                    last_byte = f.read(1)
                    if last_byte in b' \n\r':
                        end_pos -= 1
                    else:
                        break
                f.seek(0)
                with contextlib.redirect_stdout(io.StringIO()):
                    dbutils.fs.put(last_part, f.read(end_pos).decode('utf-8'), overwrite=True)

        for part in part_files:
            with open(part, 'rb') as infile:
                shutil.copyfileobj(infile, output_handle)

        try:
            rc = dbutils.fs.rm(temp_volume_base_path, True)
        except Exception:
            pass


    def read_parquet(self, parquet: ParquetFile):
        pass


    def read_csv(self, filepath):
        pass



    #
    # Transform methods
    #
    def add_out_index(self, df: "SparkDataFrame", cubemaths_helper_by_codeid: dict):
        from pyspark.sql.functions import col, lit

        for col_helper in cubemaths_helper_by_codeid.values():
            mapping = [(k, v) for k, v in col_helper._position_of_value.items()]
            mapping_df = df.sparkSession.createDataFrame(mapping, [col_helper._colname_in_dataframe, "pos"])
            
            df = df.join(mapping_df, on=col_helper._colname_in_dataframe, how="left")
            
            df = df.withColumn(
                f"int_{col_helper._colname_in_dataframe}",
                col("pos") * lit(col_helper.factor)
            )
            df = df.drop("pos") 

        columns_to_sum = [f"int_{col_helper._colname_in_dataframe}" for col_helper in cubemaths_helper_by_codeid.values()]
        return self.add_sum_column(df, "out_index", columns_to_sum)
    
    def add_sum_column(
            self, 
            df: "SparkDataFrame", 
            sum_col_name: str, 
            columns: list[str]
    ) -> "SparkDataFrame":
        
        from pyspark.sql.functions import col

        return df.withColumn(sum_col_name, reduce(operator.add, (col(c) for c in columns)))


    def merge(
            self, 
            df1: "SparkDataFrame", 
            df2: "SparkDataFrame", 
            on: str, 
            how: Literal["left", "right", "outer", "inner", "cross"] = "left"
    ) -> "SparkDataFrame":
        return df1.join(df2, on=on, how=how)




    def wide_to_long(
            self, df: "SparkDataFrame", 
            identifier_cols: list, 
            stubnames: list, 
            measurement_codes: list, 
            j_column_name: str, 
            sep: str, 
            suffix: str
    ) -> "SparkDataFrame":
        
        from pyspark.sql.functions import expr

        unpivoted_dfs = {}

        df_casted = df
        all_measurement_cols_to_cast = []
        for stub in stubnames:
            for code in measurement_codes:
                col_name = f"{stub}{sep}{code}"
                if col_name in df.columns and stub == "VALUE":
                    all_measurement_cols_to_cast.append(col_name)

        for col_to_cast in set(all_measurement_cols_to_cast):
            df_casted = df_casted.withColumn(col_to_cast, expr(f"try_cast(`{col_to_cast}` as double)"))

        for stub in stubnames:
            current_stub_cols = [f"{stub}{sep}{code}" for code in measurement_codes]

            missing_columns = [col_name for col_name in current_stub_cols if col_name not in df_casted.columns]
            if missing_columns:
                raise ValueError(f"The following columns are missing for stub '{stub}': {missing_columns}")

            stack_expr_parts = []
            for code in measurement_codes:
                stack_expr_parts.append(f"'{code}'")
                stack_expr_parts.append(f"`{stub}{sep}{code}`")

            stack_expression = f"stack({len(measurement_codes)}, {', '.join(stack_expr_parts)})"

            unpivoted_df = df_casted.selectExpr(
                *identifier_cols,
                f"{stack_expression} as ({j_column_name}, `{stub}`)"
            )
            unpivoted_dfs[stub] = unpivoted_df

        if not unpivoted_dfs:
            return df.limit(0)

        result_df = unpivoted_dfs[stubnames[0]]
        join_cols = identifier_cols + [j_column_name]

        for i in range(1, len(stubnames)):
            stub = stubnames[i]
            result_df = result_df.join(unpivoted_dfs[stub], on=join_cols, how="inner")

        final_columns_order = identifier_cols + [j_column_name] + stubnames
        result_df = result_df.select(*final_columns_order)

        return result_df


    def rename(
            self, 
            df: "SparkDataFrame", 
            rename_map: dict
    ) -> "SparkDataFrame":

        for old_name, new_name in rename_map.items():
            if old_name in df.columns:
                df = df.withColumnRenamed(old_name, new_name)
        return df


    def add_missing_symbolcolumns(
            self, 
            measurement_codes: list, 
            df: "SparkDataFrame"
    ) -> "SparkDataFrame":
        from pyspark.sql.functions import lit

        for code in measurement_codes:
            column_name = f"SYMBOL_{code}"
            if column_name not in df.columns:
                df = df.withColumn(column_name, lit(""))
        return df


    def add_missing_rows(
            self, 
            matrix_size: int, 
            missing_row_symbol: str, 
            df: "SparkDataFrame"
    ) -> "SparkDataFrame":

        spark = df.sparkSession
        out_index_df = spark.range(0, matrix_size).withColumnRenamed("id", "out_index")
        merged_df = out_index_df.join(df, on="out_index", how="left")
        merged_df = merged_df.fillna({ "out_value": missing_row_symbol })

        return merged_df.orderBy("out_index")
    

    def add_out_value(
            self, 
            df: "SparkDataFrame", 
            missing_cell_symbol: str
    ) -> "SparkDataFrame":

        from pyspark.sql.functions import when, col, lit, trim

        return df.withColumn(
            "out_value",
            when(
                col("SYMBOL").isNotNull() & (trim(col("SYMBOL")) != ""),
                col("SYMBOL").cast("string")
            ).when(
                col("VALUE").isNotNull() & (trim(col("VALUE")) != ""),
                col("VALUE").cast("string")
            ).otherwise(lit(missing_cell_symbol))
        )


    def round_by_decimals(
            self, 
            df: "SparkDataFrame", 
            measurements: List[Measurement]
    ) -> "SparkDataFrame":
        
        from pyspark.sql.functions import round as spark_round, col

        for my_cont in measurements:
            df = df.withColumn(
                my_cont.column_name, 
                spark_round(col(my_cont.column_name), Commons.get_decimals())
            )
        return df




    #
    # Utility methods
    #
    def get_columns_to_list(
            self, 
            df: "SparkDataFrame"
    ) -> List[str]:
        
        return df.columns


    def get_timeperiodes(
            self, 
            df: "SparkDataFrame", 
            column_name: str
    ) -> list:

        distinct_values = [row[column_name] for row in df.select(column_name).distinct().collect()]
        return sorted(distinct_values, reverse=False)


    def remove_trailing_zero_decimals(
            self, 
            df: "SparkDataFrame"
    ) -> "SparkDataFrame":
        
        from pyspark.sql.functions import when, col, regexp_replace

        mask = (
            col("out_value").cast("string").rlike(r"^-?\d+\.?\d*$") & 
            col("out_value").cast("string").contains(".")
        )

        df = df.withColumn(
            "out_value",
            when(~mask, col("out_value"))
            .otherwise(
                regexp_replace(
                    regexp_replace(col("out_value").cast("string"), r"0+$", ""), 
                    r"\.$", ""
                )
            )
        )
        return df



    #
    # Validation methods
    #
    def validate_codelist_vs_data_values(
            self, 
            df: "SparkDataFrame", 
            coded_dimensions: list, 
            resolved_pxcodes_ids: dict
    ) -> None:
        from pyspark.sql.functions import col

        df = df.cache()

        for coded_dim in coded_dimensions:
            dim_column_name = coded_dim.column_name
            codelist_values = [item.code for item in resolved_pxcodes_ids[coded_dim.codelist_id].valueitems]

            invalid_values = (
                df
                .filter(~col(dim_column_name).isin(codelist_values) & col(dim_column_name).isNotNull())
                .select(dim_column_name)
                .distinct()
                .limit(21)
                .collect()
            )

            if len(invalid_values) > 20:
                raise ValueError(
                    f"There are more than 20 invalid values in the data for '{dim_column_name}'."
                )
            elif invalid_values:
                missing_values = [row[dim_column_name] for row in invalid_values]
                raise ValueError(
                    f"Values {missing_values} in dataset for coded dimension '{dim_column_name}' are not in codelist '{coded_dim.codelist_id}'."
                )

    def validate_coded_values(
            self, 
            df: "SparkDataFrame", 
            column: str, 
            codelist: list
    ) -> None:
        
        from pyspark.sql.functions import col

        invalid_rows = df.filter(~col(column).isin(codelist) & ~col(column).isNull())

        if invalid_rows.limit(1).count() > 0:
            err_mess = f"There are rows with invalid values in column '{column}'."
            print(invalid_rows.limit(10).toPandas())
            raise ValueError(err_mess)
    

    def validate_data(
            self, 
            df: "SparkDataFrame", 
            data_file_path: str
    ) -> None:
        
        from pyspark.sql.functions import col
        
        # TODO: Read valid_symbol_entries from a configuration or constants file
        valid_symbol_entries = ["", ".", "..", "...", "....", ".....", "......", "-"]
        colnames = df.columns

        for col_name in colnames:
            if "." in col_name:
                raise ValueError(
                    f"Column: {col_name} has a dot, if it is not so in the datafile, there probably is a duplicate in columnname."
                )

            if col_name.endswith("_SYMBOL"):
                col_without_symbol = col_name[:-7]
                if col_without_symbol not in colnames:
                    raise ValueError(
                        f"Found {col_name}, but no matching {col_without_symbol}."
                    )

                invalid_rows = df.filter(
                    ~col(col_name).isin(valid_symbol_entries) & ~col(col_name).isNull()
                )

                # Check if there are invalid rows
                if invalid_rows.limit(1).count() > 0:
                    err_mess = f"There are rows with bad value in {col_name} column."
                    print(invalid_rows.limit(10).toPandas())
                    raise ValueError(err_mess)