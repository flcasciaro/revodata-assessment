"""Unit tests for the pure parsing helpers in `revodata_assessment.cleaning`."""

import pytest

from revodata_assessment.cleaning import (
    extract_postcode4,
    normalize_postal_code,
    parse_area_sqm,
    parse_currency,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("€ 950,-  Utilities incl.", 950.0),
        ("€ 1,-", 1.0),
        ("€ 1.250,50", 1250.5),
        (None, None),
        ("", None),
        ("no digits here", None),
    ],
)
def test_parse_currency(value: str | None, expected: float | None) -> None:
    """Parses Dutch currency strings, including thousands separators and free text."""
    assert parse_currency(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("14 m2", 14.0),
        ("115 m2", 115.0),
        ("12.5 m2", 12.5),
        (None, None),
        ("", None),
    ],
)
def test_parse_area_sqm(value: str | None, expected: float | None) -> None:
    """Parses area strings such as '14 m2' into square meters."""
    assert parse_area_sqm(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1052AB", "1052AB"),
        ("1052 AB", "1052AB"),
        ("1018  DW", "1018DW"),
        ("1091 ab", "1091AB"),
        ("Nederland 1091 TS", "1091TS"),
        ("1079 HH Amsterdam", "1079HH"),
        ("`1055tk", "1055TK"),
        ("1053", None),
        ("....", None),
        ("342HUIS", None),
        (None, None),
    ],
)
def test_normalize_postal_code(value: str | None, expected: str | None) -> None:
    """Recovers a full 6-character postal code embedded in messy free text."""
    assert normalize_postal_code(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1052AB", "1052"),
        ("1079 HH Amsterdam", "1079"),
        ("1053", "1053"),
        ("....", None),
        ("b", None),
        ("0", None),
        (None, None),
    ],
)
def test_extract_postcode4(value: str | None, expected: str | None) -> None:
    """Falls back from a full postal code to a bare 4-digit code, else None."""
    assert extract_postcode4(value) == expected
