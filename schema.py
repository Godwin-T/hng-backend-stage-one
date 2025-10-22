"""
Pydantic schemas for string analysis API payloads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StringProperties(BaseModel):
    """Computed properties describing a stored string."""

    length: int = Field(..., description="Number of characters in the string.")
    is_palindrome: bool = Field(
        ..., description="Whether the string reads the same forwards and backwards."
    )
    unique_characters: int = Field(..., description="Count of distinct characters.")
    word_count: int = Field(..., description="Number of whitespace-delimited words.")
    sha256_hash: str = Field(..., description="SHA-256 hash of the string contents.")
    character_frequency_map: Dict[str, int] = Field(
        ..., description="Mapping of characters to occurrence counts."
    )


class StringResource(BaseModel):
    """Representation of a stored string and its derived metadata."""

    id: str = Field(..., description="Unique identifier for the string resource.")
    value: str = Field(..., description="Original string value.")
    properties: StringProperties = Field(
        ..., description="Derived analytics for the string."
    )
    created_at: datetime = Field(
        ..., description="Timestamp (ISO 8601) when the string was stored."
    )


class AppliedFilters(BaseModel):
    """Filters that can be applied when listing strings."""

    is_palindrome: Optional[bool] = Field(
        None, description="Filter by palindrome status."
    )
    min_length: Optional[int] = Field(
        None, description="Filter out strings shorter than this length."
    )
    max_length: Optional[int] = Field(
        None, description="Filter out strings longer than this length."
    )
    word_count: Optional[int] = Field(
        None, description="Filter by exact number of whitespace-delimited words."
    )
    contains_character: Optional[str] = Field(
        None,
        description="Filter strings containing this character.",
        min_length=1,
        max_length=1,
    )

    class Config:
        extra = "forbid"


class StringsListResponse(BaseModel):
    """Response payload for listing strings with optional filtering."""

    data: List[StringResource]
    count: int = Field(..., description="Total number of items in the response.")
    filters_applied: Optional[AppliedFilters] = Field(
        None, description="Echo of filters used for this result set."
    )


class NaturalLanguageInterpretation(BaseModel):
    """Details of the parsed natural language filters."""

    original: str = Field(..., description="Original natural language query text.")
    parsed_filters: AppliedFilters = Field(
        ..., description="Filters inferred from the natural language query."
    )


class NaturalLanguageFilterResponse(BaseModel):
    """Response payload for natural language filter queries."""

    data: List[StringResource]
    count: int = Field(..., description="Number of strings that matched the query.")
    interpreted_query: NaturalLanguageInterpretation = Field(
        ..., description="Echo of the interpreted natural language query."
    )
