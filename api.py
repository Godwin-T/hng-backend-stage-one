"""
API endpoints for string analytics.
"""
import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import ValidationError

from utils import (
    character_frequency_map,
    is_palindrome,
    length,
    sha256_hash,
    unique_characters,
    word_count,
)
from schema import (
    AppliedFilters,
    NaturalLanguageFilterResponse,
    NaturalLanguageInterpretation,
    StringProperties,
    StringResource,
    StringsListResponse,
)

router = APIRouter(prefix="/strings", tags=["strings"])

# In-memory store keyed by exact string value.
_STRING_STORE: Dict[str, StringResource] = {}


def _build_properties(value: str) -> StringProperties:
    """Compute analytic properties for a string."""
    return StringProperties(
        length=length(value),
        is_palindrome=is_palindrome(value),
        unique_characters=unique_characters(value),
        word_count=word_count(value),
        sha256_hash=sha256_hash(value),
        character_frequency_map=character_frequency_map(value)
    )


def _build_resource(value: str, created_at: Optional[datetime] = None) -> StringResource:
    """Create a full resource representation for the provided string."""
    properties = _build_properties(value)
    return StringResource(
        id=properties.sha256_hash,
        value=value,
        properties=properties,
        created_at=created_at or datetime.utcnow()
    )


def store_string(value: str, created_at: Optional[datetime] = None) -> StringResource:
    """
    Persist a string value in the in-memory store and return its representation.

    If the string already exists, the original record is returned untouched.
    """
    existing = _STRING_STORE.get(value)
    if existing is not None:
        return existing

    resource = _build_resource(value, created_at=created_at)
    _STRING_STORE[value] = resource
    return resource


def _apply_filters(
    records: Iterable[StringResource],
    filters: AppliedFilters,
) -> List[StringResource]:
    """Filter stored strings based on the supplied filter set."""
    results: List[StringResource] = []
    for record in records:
        props = record.properties

        if filters.is_palindrome is not None and props.is_palindrome != filters.is_palindrome:
            continue
        if filters.min_length is not None and props.length < filters.min_length:
            continue
        if filters.max_length is not None and props.length > filters.max_length:
            continue
        if filters.word_count is not None and props.word_count != filters.word_count:
            continue
        if filters.contains_character is not None:
            # Perform a case-insensitive membership check.
            target = filters.contains_character.lower()
            if target not in record.value.lower():
                continue

        results.append(record)

    return results


def _parsed_filters_or_none(filters: AppliedFilters) -> Optional[AppliedFilters]:
    """Return filters if any fields are set; otherwise None."""
    if filters.model_dump(exclude_none=True):
        return filters
    return None


def _parse_natural_language_query(query: str) -> AppliedFilters:
    """
    Attempt to infer filters from natural language input.

    Raises:
        HTTPException: If parsing fails or results in conflicting filters.
    """
    normalized = query.strip().lower()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse natural language query",
        )

    inferred: Dict[str, object] = {}

    if "palindrom" in normalized:
        inferred["is_palindrome"] = True

    if "single word" in normalized or "one word" in normalized:
        inferred["word_count"] = 1

    longer_match = re.search(r"longer than\s+(\d+)\s+character", normalized)
    if longer_match:
        inferred["min_length"] = int(longer_match.group(1)) + 1

    at_least_match = re.search(r"at least\s+(\d+)\s+character", normalized)
    if at_least_match:
        inferred["min_length"] = max(
            int(at_least_match.group(1)),
            inferred.get("min_length", 0),
        )

    shorter_match = re.search(r"shorter than\s+(\d+)\s+character", normalized)
    if shorter_match:
        inferred["max_length"] = int(shorter_match.group(1)) - 1

    at_most_match = re.search(r"(?:at most|no more than)\s+(\d+)\s+character", normalized)
    if at_most_match:
        inferred["max_length"] = min(
            int(at_most_match.group(1)),
            inferred.get("max_length", int(at_most_match.group(1))),
        )

    letter_match = re.search(r"(?:letter|character)\s+([a-z])", normalized)
    if letter_match:
        inferred["contains_character"] = letter_match.group(1)

    if "first vowel" in normalized:
        inferred["contains_character"] = "a"

    contains_letter_match = re.search(
        r"contain(?:ing)? the letter\s+([a-z])", normalized
    )
    if contains_letter_match:
        inferred["contains_character"] = contains_letter_match.group(1)

    if not inferred:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse natural language query",
        )

    try:
        filters = AppliedFilters(**inferred)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parsed but resulted in conflicting filters",
        ) from exc

    if (
        filters.min_length is not None
        and filters.max_length is not None
        and filters.min_length > filters.max_length
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parsed but resulted in conflicting filters",
        )

    return filters


@router.get(
    "/{string_value}",
    response_model=StringResource,
    responses={
        404: {"description": "String does not exist in the system"},
    },
)
def get_string(string_value: str) -> StringResource:
    """Retrieve a specific string resource by its exact value."""
    resource = _STRING_STORE.get(string_value)
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system",
        )
    return resource


@router.get(
    "",
    response_model=StringsListResponse,
    responses={
        400: {"description": "Invalid query parameter values or types"},
    },
)
def list_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None, ge=0),
    max_length: Optional[int] = Query(None, ge=0),
    word_count: Optional[int] = Query(None, ge=0),
    contains_character: Optional[str] = Query(None, min_length=1, max_length=1),
) -> StringsListResponse:
    """Retrieve all stored strings, optionally filtered by supplied criteria."""
    if (
        min_length is not None
        and max_length is not None
        and min_length > max_length
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query parameter values or types",
        )

    try:
        filters = AppliedFilters(
            is_palindrome=is_palindrome,
            min_length=min_length,
            max_length=max_length,
            word_count=word_count,
            contains_character=contains_character,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query parameter values or types",
        ) from exc

    filtered_records = _apply_filters(_STRING_STORE.values(), filters)
    return StringsListResponse(
        data=filtered_records,
        count=len(filtered_records),
        filters_applied=_parsed_filters_or_none(filters),
    )


@router.get(
    "/filter-by-natural-language",
    response_model=NaturalLanguageFilterResponse,
    responses={
        400: {"description": "Unable to parse natural language query"},
        422: {"description": "Query parsed but resulted in conflicting filters"},
    },
)
def filter_by_natural_language(query: str = Query(...)) -> NaturalLanguageFilterResponse:
    """Filter stored strings based on a natural language query."""
    filters = _parse_natural_language_query(query)
    filtered_records = _apply_filters(_STRING_STORE.values(), filters)
    interpretation = NaturalLanguageInterpretation(
        original=query,
        parsed_filters=filters,
    )
    return NaturalLanguageFilterResponse(
        data=filtered_records,
        count=len(filtered_records),
        interpreted_query=interpretation,
    )


@router.delete(
    "/{string_value}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "String does not exist in the system"},
    },
)
def delete_string(string_value: str) -> None:
    """Delete a stored string by its exact value."""
    if string_value not in _STRING_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system",
        )
    _STRING_STORE.pop(string_value, None)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=StringResource,
    responses={
        400: {"description": 'Invalid request body or missing "value" field'},
        409: {"description": "String already exists in the system"},
        422: {"description": 'Invalid data type for "value" (must be string)'},
    },
)
def create_string(payload: dict = Body(...)) -> StringResource:
    """Create or analyze a string, returning its computed properties."""
    if "value" not in payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid request body or missing "value" field',
        )

    value = payload["value"]

    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Invalid data type for "value" (must be string)',
        )

    if value in _STRING_STORE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="String already exists in the system",
        )

    return store_string(value)
