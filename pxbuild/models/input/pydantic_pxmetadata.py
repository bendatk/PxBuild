# generated by datamodel-codegen:
#   filename:  pxmetadata.yaml
#   timestamp: 2024-02-05T14:29:33+00:00

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    column_name: Optional[str] = Field(None, alias="columnName")
    """
    name of column in dataset
    """
    code: Optional[str] = None
    """
    the code of the measurement
    """
    codelist_id: Optional[str] = Field(None, alias="codelistId")
    """
    A Link to a PxCodes document
    """


class LabelConstructionOption(Enum):
    """
    Construct label for codelist entry as text or code or text then code or code then text
    """

    code = "code"
    text = "text"
    code_text = "code_text"
    text_code = "text_code"


class PriceType(Enum):
    """
    Empty if not a price
    """

    current = "Current"
    fixed = "Fixed"


class AttachmentItem(BaseModel):
    dimension_code: str = Field(..., alias="dimensionCode")
    """
    The code of the dimension (found in config for time and measure)
    """
    value_code: str = Field(..., alias="valueCode")
    """
    The code of the Value
    """


class TimeDimension(BaseModel):
    column_name: Optional[str] = Field(None, alias="columnName")
    """
    name of column in dataset
    """
    time_period_format: Optional[str] = Field(None, alias="timePeriodFormat")
    """
    example: yyyy
    """
    label: Optional[Dict[str, str]] = None


class CellNote(BaseModel):
    """
    Note on a cell/subcube
    """

    attachment: List[AttachmentItem]
    """
    Attaches the text on a point/subcube of the cube. The array has one or zero entries for each dimension. No entry for a dimension means everything.
    """
    text: Dict[str, str]
    is_mandatory: bool = Field(..., alias="isMandatory")


class Note(BaseModel):
    text: Dict[str, str]
    is_mandatory: bool = Field(..., alias="isMandatory")


class CodedDimension(BaseModel):
    column_name: str = Field(..., alias="columnName")
    """
    name of column in dataset
    """
    code: Optional[str] = None
    """
    the code of the dimention( aka variable). Defaults to columName if missing
    """
    is_geo_variable_type: Optional[bool] = Field(False, alias="isGeoVariableType")
    """
    Geo variable or not
    """
    codelist_id: str = Field(..., alias="codelistId")
    """
    A Link to a PxCodes document
    """
    label_construction_option: Optional[LabelConstructionOption] = Field("text", alias="labelConstructionOption")
    """
    Construct label for codelist entry as text or code or text then code or code then text
    """
    label: Optional[Dict[str, str]] = None
    doublecolumn: Optional[bool] = False
    """
    Applies only to some of the file-export formats. See DOUBLECOLUMN-keyword
    """
    notes: Optional[List[Note]] = None
    meta_id: Optional[List[str]] = Field(None, alias="metaId")
    """
    For MetaId keyword
    """


class Measurement(BaseModel):
    column_name: str = Field(..., alias="columnName")
    """
    name of column in dataset
    """
    code: Optional[str] = None
    """
    the code of the measurement. Defaults to columName if missing
    """
    label: Dict[str, str]
    show_decimals: int = Field(..., alias="showDecimals")
    """
    number of decimal to use in output
    """
    price_type: Optional[PriceType] = Field(None, alias="priceType")
    """
    Empty if not a price
    """
    is_seasonally_adjusted: Optional[bool] = Field(False, alias="isSeasonallyAdjusted")
    is_workingdays_adjusted: Optional[bool] = Field(False, alias="isWorkingdaysAdjusted")
    aggregation_allowed: bool = Field(..., alias="aggregationAllowed")
    """
    Is it meaningfull to sum this measurement
    """
    base_period: Optional[Dict[str, str]] = Field(None, alias="basePeriod")
    """
    For index example: '1. kvartal 2010'
    """
    reference_period: Optional[Dict[str, str]] = Field(None, alias="referencePeriod")
    """
    Text with information on the reference period for the statistics.
    """
    rank: Optional[Dict[str, str]] = None
    """
    Sort order for measurement in dimension, document order is default
    """
    unit_of_measure: Dict[str, str] = Field(..., alias="unitOfMeasure")
    """
    Text including unit multiplier
    """
    notes: Optional[List[Note]] = None
    meta_id: Optional[List[str]] = Field(None, alias="metaId")
    """
    For MetaId keyword
    """


class Dataset(BaseModel):
    """
    Payload
    """

    table_id: str = Field(..., alias="tableId")
    """
    example: '07459' To be used as id in PxWeb Url
    """
    stored_decimals: Optional[int] = Field(None, alias="storedDecimals")
    """
    How many decimals should be stored in the PxFile. Default is the max number of decimals shown.
    """
    statistics_id: Optional[str] = Field(None, alias="statisticsId")
    """
    Id of group of tables in the registry of statistics. example: '8765'
    """
    data_file: Optional[str] = Field(None, alias="dataFile")
    """
    TODO: Er dette en filsti eller en url. required? Adress to the parquet-file with datadata
    """
    base_title: Dict[str, str] = Field(..., alias="baseTitle")
    """
    Text to which tableid is prefixed and _by_ variable list is appended. Is used for the CONTENTS keyword. example: no Utenrikshandel med varer
    """
    search_keywords: Optional[Dict[str, List[str]]] = Field(None, alias="searchKeywords")
    """
    Array of keywords by language for search. Is used for the SYNONYMS keyword. example:'{en: [External trade, export]}'
    """
    notes: Optional[List[Note]] = None
    cell_notes: Optional[List[CellNote]] = Field(None, alias="cellNotes")
    time_dimension: TimeDimension = Field(..., alias="timeDimension")
    coded_dimensions: Optional[List[CodedDimension]] = Field(None, alias="codedDimensions")
    """
    Also known as classification variables
    """
    measurements: List[Measurement]
    """
    Also known as content variables
    """
    meta_id: Optional[List[str]] = Field(None, alias="metaId")
    """
    For MetaId keyword
    """
    row_missing: Optional[str] = Field(".", alias="rowMissing")
    """
    Value to insert in data when row is missing.
    """
    cell_missing: Optional[str] = Field(".", alias="cellMissing")
    """
    Value to insert in data when cell is missing.
    """
    official_statistics: Optional[bool] = Field(False, alias="officialStatistics")
    copyright: Optional[bool] = False
    first_published: Optional[str] = Field(None, alias="firstPublished")
    """
    The date when the data cube was first published in the format CCYYMMDD hh:mm
    """
    attributes: Optional[List[Attribute]] = None


class PxMetadata(BaseModel):
    """
    Outer class
    """

    dataset: Dataset
    """
    Payload
    """
