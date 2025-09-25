import operator, os, shutil
from typing import Literal, List
from pyarrow.parquet import ParquetFile
from pyspark.dbutils import DBUtils
from io import TextIOWrapper
from functools import reduce
from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType
from pyspark.sql.functions import struct, sort_array, row_number, round as spark_round, expr, lit, when, col, regexp_replace
from pyspark.sql.functions import trim, row_number, collect_list, concat_ws, monotonically_increasing_id
from .....models.output.pxfile.util.commons import Commons
from .....models.output.pxfile.keywords._data import _PxData
from .....models.input.pydantic_pxmetadata import Measurement
from ._backend_methods import IBackendMethods

class SparkWrapper(IBackendMethods):

    @property
    def backend_name(self) -> str:
        return "spark"
    
    @staticmethod
    def get_spark() -> SparkSession:
        try:
            from databricks.connect import DatabricksSession
            return DatabricksSession.builder.getOrCreate()
        except ImportError:
            return SparkSession.builder.getOrCreate()
        
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
        output_file_handle: TextIOWrapper, # Already opened file handle for writing
        temp_volume_base_path: str,      # Base path for temporary chunk files (e.g., "/Volumes/catalog/schema/volume/temp_chunks")
        columns_per_line: int,
        chunk_size: int = 500000
    ) -> None:

        temp_output_path = None
        path_to_list = None
        try:
            if str(type(data._data)) not in self.SPARKDATAFRAMETYPES:
                raise TypeError(f"Input 'data' must be a Spark DataFrame, got {type(data._data)}")
            if not isinstance(output_file_handle, TextIOWrapper):
                raise TypeError(f"Input 'output_file_handle' must be a TextIOWrapper, got {type(output_file_handle)}")
            if not temp_volume_base_path.startswith("/Volumes/"):
                print("Warning: temp_volume_base_path does not start with '/Volumes/'. Ensure it's a valid Databricks Volume path.")
            if "out_value" not in data._data.columns:
                raise ValueError("Input DataFrame must contain a column named 'out_value'.")

            df = data._data.select("out_value")


            df_temp_id = df.withColumn("_temp_id", monotonically_increasing_id()).withColumn("_dummy_partition", lit(1))
            window_spec_global_order = Window.partitionBy("_dummy_partition").orderBy("_temp_id")
            df_with_rownum = df_temp_id.withColumn("_global_row_num", row_number().over(window_spec_global_order)).drop("_temp_id", "_dummy_partition")

            # Calculate line groups and assign a "chunk_id" so that both change at the same row boundary
            # We are doing this to ensure that each chunk contains a complete set of lines
            rows_per_chunk = ((chunk_size + columns_per_line - 1) // columns_per_line) * columns_per_line

            df_with_chunk = df_with_rownum.withColumn(
                "line_group",
                ((col("_global_row_num") - 1) / columns_per_line).cast("int")
            ).withColumn(
                "chunk_id",
                ((col("_global_row_num") - 1) / rows_per_chunk).cast("int")
            )

            # Repartition by chunk_id to enhance parallelism
            df_with_chunk = df_with_chunk.repartition("chunk_id")

            # Group by chunk_id and line_group, then collect values and format lines
            # Add a space after each line_group by appending it to the formatted line as a string
            df_grouped_and_formatted = df_with_chunk \
                .withColumn("out_value_struct", struct(col("_global_row_num"), col("out_value"))) \
                .groupBy("chunk_id", "line_group") \
                .agg(collect_list("out_value_struct").alias("line_data_struct")) \
                .withColumn("line_data_struct", sort_array(col("line_data_struct"))) \
                .withColumn("line_data", expr("transform(line_data_struct, x -> x.out_value)")) \
                .withColumn("formatted_line", concat_ws(" ", col("line_data"))) \
                .withColumn("formatted_line", concat_ws("", col("formatted_line"), lit(" "))) \
                .select("chunk_id", "line_group", "formatted_line")
            
            # Re-apply ordering within each chunk to maintain row order
            df_ordered_for_write = df_grouped_and_formatted.orderBy("chunk_id", "line_group")

            # Write each chunk to a temporary directory
            spark = data._data.sparkSession
            temp_dir_name = f"temp_chunk_{os.urandom(4).hex()}"
            if temp_volume_base_path.endswith(".px"):
                temp_volume_base_path = temp_volume_base_path[:-3]
            temp_output_path = os.path.join(temp_volume_base_path, temp_dir_name)

            df_output_for_text = df_ordered_for_write.select("chunk_id", "formatted_line")
            
            df_output_for_text.write \
                .partitionBy("chunk_id") \
                .mode("overwrite") \
                .text(temp_output_path)
            
            
            dbutils = DBUtils(spark)
            files = dbutils.fs.ls(temp_output_path)
            chunk_id_and_file = []
            for f in files:
                if f.isDir() and f.name.startswith("chunk_id="):
                    chunk_id = int(f.name.split("chunk_id=")[1].rstrip("/"))
                    part_files = dbutils.fs.ls(f.path)
                    for pf in part_files:
                        if pf.name.startswith("part-"):
                            local_path = pf.path
                            if local_path.startswith("dbfs:/"):
                                local_path = local_path.replace("dbfs:", "")
                            chunk_id_and_file.append((chunk_id, local_path))

            # Sort by chunk_id
            chunk_id_and_file.sort(key=lambda x: x[0])
            all_part_files = [file for _, file in chunk_id_and_file]

            # Read from temporary files and write to the provided output_file_handle
            # Ensure the last line does not end with a newline character
            is_last_file = False
            num_files = len(all_part_files)
            for idx, part_file_uri in enumerate(all_part_files):
                is_last_file = (idx == num_files - 1)
                try:
                    with open(part_file_uri, "r") as infile:
                        if not is_last_file:
                            shutil.copyfileobj(infile, output_file_handle)
                        else:
                            lines = infile.readlines()
                            if lines:
                                for line in lines[:-1]:
                                    output_file_handle.write(line)
                                output_file_handle.write(lines[-1].rstrip('\n').rstrip(' '))
                                
                except Exception as e:
                    print(f"Error reading from temporary file {part_file_uri}: {e}")
                    raise
        except Exception as e:
            print(f"Error writing DATA part to file handle: {e}")
            raise
        finally:
            if temp_output_path is not None:
                try:
                    dbutils = DBUtils(data._data.sparkSession)
                    try:
                        dbutils.fs.ls(temp_output_path)
                        dbutils.fs.rm(temp_output_path, True)
                    except Exception:
                        pass
                except Exception as cleanup_e:
                    print(f"Error during temporary directory cleanup: {cleanup_e}")

    def read_parquet(self, parquet: ParquetFile):
        pass


    def read_csv(self, filepath):
        pass



    #
    # Transform methods
    #
    def add_out_index(
            self, 
            df: SparkDataFrame, 
            cubemaths_helper_by_codeid: dict
    ) -> SparkDataFrame:
        
        columns_to_sum = []

        for col_helper in cubemaths_helper_by_codeid.values():
            contrib_col_name = f"int_{col_helper._colname_in_dataframe}"
            case_expr = "CASE"
            for value, pos in col_helper._position_of_value.items():
                case_expr += f" WHEN `{col_helper._colname_in_dataframe}` = '{value}' THEN {pos}"
            case_expr += " ELSE 0 END"
            position_expr = f"{col_helper.factor} * ({case_expr})"

            df = df.withColumn(
                contrib_col_name,
                expr(position_expr).alias(contrib_col_name)
            )
            columns_to_sum.append(contrib_col_name)

        return self.add_sum_column(df, "out_index", columns_to_sum)


    def add_sum_column(
            self, 
            df: SparkDataFrame, 
            sum_col_name: str, 
            columns: list[str]
    ) -> SparkDataFrame:
        
        return df.withColumn(sum_col_name, reduce(operator.add, (col(c) for c in columns)))


    def merge(
            self, 
            df1: SparkDataFrame, 
            df2: SparkDataFrame, 
            on: str, 
            how: Literal["left", "right", "outer", "inner", "cross"] = "left"
    ) -> SparkDataFrame:
        return df1.join(df2, on=on, how=how)




    def wide_to_long(
            self, df: SparkDataFrame, 
            identifier_cols: list, 
            stubnames: list, 
            measurement_codes: list, 
            j_column_name: str, 
            sep: str, 
            suffix: str
    ) -> SparkDataFrame:
        
        unpivoted_dfs = {}

        df_casted = df
        all_measurement_cols_to_cast = []
        for stub in stubnames:
            for code in measurement_codes:
                col_name = f"{stub}{sep}{code}"
                if col_name in df.columns:
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
            df: SparkDataFrame, 
            rename_map: dict
    ) -> SparkDataFrame:

        for old_name, new_name in rename_map.items():
            if old_name in df.columns:
                df = df.withColumnRenamed(old_name, new_name)
        return df


    def add_missing_symbolcolumns(
            self, 
            measurement_codes: list, 
            df: SparkDataFrame
    ) -> SparkDataFrame:
        
        for code in measurement_codes:
            column_name = f"SYMBOL_{code}"
            if column_name not in df.columns:
                df = df.withColumn(column_name, lit(""))
        return df


    def add_missing_rows(
            self, 
            matrix_size: int, 
            missing_row_symbol: str, 
            df: SparkDataFrame
    ) -> SparkDataFrame:
        spark = df.sparkSession
        out_index_df = spark.range(0, matrix_size).withColumnRenamed("id", "out_index")
        merged_df = out_index_df.join(df, on="out_index", how="left")
        merged_df = merged_df.fillna({ "out_value": missing_row_symbol })

        return merged_df.orderBy("out_index")
    

    def add_out_value(
            self, 
            df: SparkDataFrame, 
            missing_cell_symbol: str
    ) -> SparkDataFrame:
        
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
            df: SparkDataFrame, 
            measurements: List[Measurement]
    ) -> SparkDataFrame:
        
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
            df: SparkDataFrame
    ) -> List[str]:
        
        return df.columns


    def get_timeperiodes(
            self, 
            df: SparkDataFrame, 
            column_name: str
    ) -> list:

        distinct_values = [row[column_name] for row in df.select(column_name).distinct().collect()]
        return sorted(distinct_values, reverse=False)


    def remove_trailing_zero_decimals(
            self, 
            df: SparkDataFrame
    ) -> SparkDataFrame:

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
            df: SparkDataFrame, 
            coded_dimensions: list, 
            resolved_pxcodes_ids: dict
    ) -> None:
    
        for coded_dim in coded_dimensions:
            dim_code = coded_dim.code
            dim_values = [row[dim_code] for row in df.select(dim_code).distinct().collect()]
            codelist_values = [item.code for item in resolved_pxcodes_ids[coded_dim.codelist_id].valueitems]
            
            missing_values = [value for value in dim_values if value not in codelist_values]
            if missing_values:
                raise ValueError(
                    'Values {} in dataset for coded dimension "{}" are not in codelist "{}".'.format(
                        ', '.join(f'"{x}"' for x in missing_values), dim_code, coded_dim.codelist_id
                    )
                )


    def validate_coded_values(
            self, 
            df: SparkDataFrame, 
            column: str, 
            codelist: list
    ) -> None:

        invalid_rows = df.filter(~col(column).isin(codelist) & ~col(column).isNull())

        if invalid_rows.count() > 0:
            err_mess = f"There are rows with invalid values in column '{column}'."
            invalid_rows.show(10)
            raise ValueError(err_mess)
    

    def validate_data(
            self, 
            df: SparkDataFrame, 
            data_file_path: str
    ) -> None:
        
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
                if invalid_rows.count() > 0:
                    err_mess = f"There are rows with bad value in {col_name} column."
                    invalid_rows.show(10)
                    raise ValueError(err_mess)