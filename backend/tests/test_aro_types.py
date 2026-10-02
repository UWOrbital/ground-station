from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from app.api.aro.schemas.auth.requests import CallsignRequest
from app.api.aro.schemas.types import (
    AddressField,
    GeneralLocationField,
    PostalCode,
    QualLevels,
)

address = TypeAdapter(AddressField)
location = TypeAdapter(GeneralLocationField)
postal = TypeAdapter(PostalCode)
qual_levels = TypeAdapter(QualLevels)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("188 Millwood Drive", "188 MILLWOOD DRIVE"),
        ('"188 Millwood Drive"', "188 MILLWOOD DRIVE"),
        ("P.O. Box 33", "PO BOX 33"),
        ("476, rue de l'Érablière", "476, RUE DE L'ERABLIERE"),
        ("  12   Main\tSt  ", "12 MAIN ST"),
        ("12\xa0Main St", "12 MAIN ST"),
        ("BOX 1137, 4790 TEBO AVE", "BOX 1137, 4790 TEBO AVE"),
        ("RR # 3", "RR # 3"),
        ("Unit 4/12-345 Main St (rear)", "UNIT 4/12-345 MAIN ST (REAR)"),
    ],
)
def test_address_normalizes_to_registry_shape(raw: str, expected: str) -> None:
    """User-typed addresses normalize to the uppercase ASCII form the registry stores."""
    assert address.validate_python(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        '""',
        "北京路 123",
        "12 Main St <script>",
        "12 Main St; DROP",
        "A" * 256,
        12,
    ],
)
def test_address_rejects_invalid(raw: Any) -> None:
    """Blank, non-Latin, junk-punctuated, over-length, and non-string addresses are rejected."""
    with pytest.raises(ValidationError):
        address.validate_python(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Jonquière", "JONQUIERE"),
        ("St. Thomas", "ST THOMAS"),
        ("Ste-Catherine de Jacques Cartier", "STE-CATHERINE DE JACQUES CARTIER"),
        ("on", "ON"),
        ("A" * 100, "A" * 100),
    ],
)
def test_general_location_normalizes(raw: str, expected: str) -> None:
    """City and province text normalizes to registry shape, up to 100 characters."""
    assert location.validate_python(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "A" * 101])
def test_general_location_rejects_invalid(raw: str) -> None:
    """Blank and over-length locations are rejected."""
    with pytest.raises(ValidationError):
        location.validate_python(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("K1A0B1", "K1A0B1"),
        ("k1a 0b1", "K1A0B1"),
        ("K1A-0B1", "K1A0B1"),
        ("  K1A 0B1 ", "K1A0B1"),
        ("L0N 1M0 ", "L0N1M0"),
        ("K1W0Z1", "K1W0Z1"),
    ],
)
def test_postal_code_normalizes(raw: str, expected: str) -> None:
    """Postal codes compact to the registry's A1A1A1 form; W and Z are allowed after the first letter."""
    assert postal.validate_python(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "GOX2V0",  # letter O where a digit belongs; a real typo present in the registry
        "D1A0B1",  # D is never used
        "K1D0B1",
        "W1A0B1",  # W and Z never lead
        "Z1A0B1",
        "K١A0B1",  # Arabic-Indic digit: [0-9], not \d, so this can't slip through
        "K1A0B",
        "K1A0B12",
        "",
        12345,
    ],
)
def test_postal_code_rejects_invalid(raw: Any) -> None:
    """Malformed, forbidden-letter, non-ASCII-digit, and wrong-length postal codes are rejected."""
    with pytest.raises(ValidationError):
        postal.validate_python(raw)


@pytest.mark.parametrize("raw", [[True] * 4, [True] * 6, []])
def test_qual_levels_requires_exactly_five(raw: list[bool]) -> None:
    """Qualification levels must be exactly five booleans, one per level A..E."""
    with pytest.raises(ValidationError):
        qual_levels.validate_python(raw)


def test_callsign_request_normalizes_full_form() -> None:
    """A fully filled form normalizes every field into registry shape."""
    request = CallsignRequest.model_validate(
        {
            "call_sign": " va1aa ",
            "personal_address": "188 Millwood Dr.",
            "personal_city": "Middle Sackville",
            "personal_province": "ns",
            "personal_postal_code": "b4e 2x8",
            "qual_levels": [True, False, True, True, False],
            "club_name": "Yarmouth Amateur Radio Club Inc.",
        }
    )

    assert request.call_sign == "VA1AA"
    assert request.personal_address == "188 MILLWOOD DR"
    assert request.personal_city == "MIDDLE SACKVILLE"
    assert request.personal_province == "NS"
    assert request.personal_postal_code == "B4E2X8"
    assert request.club_name == "YARMOUTH AMATEUR RADIO CLUB INC"


def test_callsign_request_minimal_form_defaults_to_none() -> None:
    """Only call_sign and qual_levels are required; omitted fields default to None."""
    request = CallsignRequest.model_validate(
        {"call_sign": "VA1AA", "qual_levels": [False] * 5}
    )

    assert request.personal_address is None
    assert request.personal_postal_code is None
    assert request.club_province is None


@pytest.mark.parametrize(
    "extra",
    [
        {"postal_code": "K1A0B1"},  # misspelled field name
        {"personal_address": ""},  # blank optional field
        {"call_sign": "VA1"},  # too short
    ],
)
def test_callsign_request_rejects_invalid(extra: dict[str, Any]) -> None:
    """Unknown keys, blank optional fields, and bad callsigns are rejected outright."""
    with pytest.raises(ValidationError):
        CallsignRequest.model_validate(
            {"call_sign": "VA1AA", "qual_levels": [False] * 5, **extra}
        )
