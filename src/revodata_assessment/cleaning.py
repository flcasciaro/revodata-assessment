"""Pure parsing helpers for cleaning raw Kamernet and Airbnb fields.

These are plain Python functions (no Spark dependency) so they can be unit
tested in isolation, then wrapped as Spark UDFs in the pipeline transformations.
"""

import re

_CURRENCY_PATTERN = re.compile(r"(\d[\d.,]*)")
_AREA_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*m2", re.IGNORECASE)
_POSTAL_CODE_PATTERN = re.compile(r"(\d{4})\s*([A-Z]{2})")
_POSTCODE4_PATTERN = re.compile(r"^(\d{4})$")


def parse_currency(value: str | None) -> float | None:
    """Parse a Dutch currency string, e.g. '€ 950,-  Utilities incl.', into a float.

    Kamernet renders monetary amounts with a euro sign, a '.' thousands
    separator and a ',' decimal separator, sometimes followed by free text.
    Returns None when no numeric amount can be found.
    """
    if not value:
        return None
    match = _CURRENCY_PATTERN.search(value)
    if not match:
        return None
    numeric = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(numeric)
    except ValueError:
        return None


def parse_area_sqm(value: str | None) -> float | None:
    """Parse an area string, e.g. '14 m2', into a float number of square meters."""
    if not value:
        return None
    match = _AREA_PATTERN.search(value)
    if not match:
        return None
    return float(match.group(1))


def normalize_postal_code(value: str | None) -> str | None:
    """Extract and normalize a full 6-character Dutch postal code, e.g. '1052AB'.

    Postal codes in both sources are inconsistently formatted: a space
    between digits and letters, extra free text (city names, stray
    punctuation), or inconsistent casing. This searches anywhere in the
    input for the 'NNNN LL' pattern and returns the upper-cased, space-free
    form, or None when no such pattern exists.
    """
    if not value:
        return None
    match = _POSTAL_CODE_PATTERN.search(value.upper())
    if not match:
        return None
    return f"{match.group(1)}{match.group(2)}"


def extract_postcode4(value: str | None) -> str | None:
    """Extract the 4-digit postal code prefix used for aggregation in this project.

    Tries a full 6-character postal code first (see `normalize_postal_code`),
    then falls back to a bare 4-digit code (Airbnb sometimes only records the
    digits). Returns None when neither pattern can be found, which signals
    that a geo-based backfill is needed.
    """
    normalized = normalize_postal_code(value)
    if normalized:
        return normalized[:4]
    if not value:
        return None
    match = _POSTCODE4_PATTERN.match(value.strip())
    if match:
        return match.group(1)
    return None
