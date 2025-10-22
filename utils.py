"""
String analysis utilities for utils.
"""


import hashlib
from collections import Counter


def length(value: str) -> int:
    """Return the number of characters in the input string."""
    return len(value)


def is_palindrome(value: str) -> bool:
    """
    Check if the string reads the same forwards and backwards.

    Comparison ignores case and leading/trailing whitespace.
    """
    normalized = value.strip().casefold()
    return normalized == normalized[::-1]


def unique_characters(value: str) -> int:
    """Count distinct characters in the string."""
    return len(set(value))


def word_count(value: str) -> int:
    """Return how many whitespace-delimited words are in the string."""
    return len(value.split())


def sha256_hash(value: str) -> str:
    """Compute the SHA-256 hash of the string and return the hex digest."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def character_frequency_map(value: str) -> dict[str, int]:
    """Return a mapping of each character to its occurrence count."""
    return dict(Counter(value))
