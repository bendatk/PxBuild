# generated by datamodel-codegen:
#   filename:  pxstatistics.yaml
#   timestamp: 2024-02-05T14:27:23+00:00

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Contact(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    """
    Personal or functional
    """
    name: Optional[Dict[str, str]] = None
    """
    Name of contact in all languages. Personal or functional
    """
    raw: Optional[Dict[str, str]] = None
    """
    If this has value it replaces the 3 other fields, so they are ignored. Anything, will be put under contact as is.
    """


class PxStatistics(BaseModel):
    """
    Holds information of a publishing system nature, or registry of statistics if you like. The asumption behind subjectCode and subjectText is that your tables may be put in a menu tree. Subject is the first level in that tree.
    """

    id: str
    """
    Id of a group of tables in the registry of statistics. example: 8765
    """
    update_frequency: Optional[Dict[str, str]] = Field(None, alias="updateFrequency")
    """
    Not in use. Must mean the same in all languages. example: Quarterly
    """
    meta_id: Optional[List[str]] = Field(None, alias="metaId")
    """
    Will be added to METAID on table level. 'KORTNAVN:kpi' lead to https://www.ssb.no/en/priser-og-prisindekser/konsumpriser/statistikk/konsumprisindeksen#om-statistikken
    """
    subject_code: str = Field(..., alias="subjectCode")
    """
    example: be
    """
    subject_text: Dict[str, str] = Field(..., alias="subjectText")
    """
    example en:Population
    """
    upcoming_releases: Optional[List[str]] = Field(None, alias="upcomingReleases")
    """
    List of dates. The first will be used for LAST-UPDATE, the next will be used for NEXT-UPDATE. example format: 2024-02-05 08:00:00.0 (to do)
    """
    contacts: List[Contact]
    """
    Will be used for CONTACT
    """
