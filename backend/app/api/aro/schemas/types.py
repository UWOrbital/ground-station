"""
Shared field types for ARO request/response schemas.

Each type normalizes its input before validating it, so everything downstream
sees a single canonical form. Types that are compared against the government
callsign registry normalize into the registry's own shape (uppercase ASCII).

Location and name types carry PII: they are validated here, compared, and
never logged or persisted.
"""

import unicodedata
from typing import Annotated

import phonenumbers
from pydantic import AfterValidator, BeforeValidator, EmailStr, Field
from pydantic.types import StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

from app.config.data_values import (
    CALL_SIGN_MAX_LENGTH,
    CALL_SIGN_MIN_LENGTH,
    DEFAULT_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
    GENERAL_LOCATION_MAX_LENGTH,
    POSTAL_CODE_LENGTH,
    QUAL_LEVEL_COUNT,
)

# -----------------------------------------------------------------
# Normalizers
# -----------------------------------------------------------------

# The registry contains no periods ("PO BOX 33", "ST THOMAS") and its CSV
# wraps addresses in literal quotes, so both are dropped from user input.
_REGISTRY_STRIP_CHARS = str.maketrans("", "", '".')


def normalize_email(email: str) -> str:
    """
    Enforce email length and lowercase the local part.

    :param email: an address already validated as an EmailStr.
    :return: the address with its local part lowercased.
    """
    if len(email) < EMAIL_MIN_LENGTH:
        raise ValueError(f"Email cannot be shorter than {EMAIL_MIN_LENGTH} characters.")
    localpart, domain = email.split("@", 1)
    return f"{localpart.lower()}@{domain}"


def normalize_registry_text(value: str) -> str:
    """
    Normalize free text into the shape the callsign registry stores it in.

    Folds accents, drops quotes and periods, collapses whitespace, and uppercases.

    :param value: raw field text.
    :return: the normalized text.
    """
    # Drop combining marks only "è" -> "e"
    folded = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))

    return " ".join(folded.translate(_REGISTRY_STRIP_CHARS).split()).upper()


def normalize_postal_code(value: str) -> str:
    """
    Normalize a Canadian postal code to the registry's compact form.

    :param value: raw field text, e.g. "k1a 0b1" or "K1A-0B1".
    :return: uppercase code with spaces and hyphens removed
    """
    return "".join(value.split()).replace("-", "").upper()


def _validate_registry_text(value: object) -> object:
    """
    Apply registry normalization, leaving non-strings for pydantic to reject.

    :param value: raw field input of any type.
    :return: the normalized string, or the original value
    """
    return normalize_registry_text(value) if isinstance(value, str) else value


def _validate_postal_code(value: object) -> object:
    """
    Apply postal-code normalization, leaving non-strings for pydantic to reject.

    :param value: raw field input of any type.
    :return: the normalized string, or the original value
    """
    return normalize_postal_code(value) if isinstance(value, str) else value


# -----------------------------------------------------------------
# Identity
# -----------------------------------------------------------------

NameField = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=DEFAULT_MAX_LENGTH, strip_whitespace=True, pattern=r"^[A-Za-zÀ-ÿ'\s\-]+$"
    ),
    AfterValidator(str.title),
]
FirstName = NameField
LastName = NameField

AROEmailField = Annotated[EmailStr, AfterValidator(normalize_email)]

PhoneNumber = Annotated[str | phonenumbers.PhoneNumber, PhoneNumberValidator(number_format="E164", default_region="CA")]

# -----------------------------------------------------------------
# Callsign registry
# -----------------------------------------------------------------

CallSign = Annotated[
    str,
    StringConstraints(
        min_length=CALL_SIGN_MIN_LENGTH, max_length=CALL_SIGN_MAX_LENGTH, to_upper=True, strip_whitespace=True
    ),
]

# Positional: index 0..4 map to qualification levels A..E.
QualLevels = Annotated[list[bool], Field(min_length=QUAL_LEVEL_COUNT, max_length=QUAL_LEVEL_COUNT)]

_RegistryText = Annotated[
    str,
    BeforeValidator(_validate_registry_text),
    StringConstraints(min_length=1, max_length=GENERAL_LOCATION_MAX_LENGTH),
]
ClubName = _RegistryText

# -----------------------------------------------------------------
# Location (PII)
# -----------------------------------------------------------------

AddressField = Annotated[
    str,
    BeforeValidator(_validate_registry_text),
    StringConstraints(min_length=1, max_length=DEFAULT_MAX_LENGTH, pattern=r"^[A-Z0-9 ,#'/&():-]+$"),
]

# City / province are length-limited only. Province is a closed set of 13 codes, change to a Literal if needed
GeneralLocationField = _RegistryText

# Canada Post never uses D, F, I, O, Q, U, and never starts a code with W or Z.
PostalCode = Annotated[
    str,
    BeforeValidator(_validate_postal_code),
    StringConstraints(
        min_length=POSTAL_CODE_LENGTH,
        max_length=POSTAL_CODE_LENGTH,
        pattern=r"^[ABCEGHJ-NPRSTVXY][0-9][ABCEGHJ-NPRSTV-Z][0-9][ABCEGHJ-NPRSTV-Z][0-9]$",
    ),
]

# -----------------------------------------------------------------
# Auth
# -----------------------------------------------------------------

AccessToken = Annotated[str, StringConstraints(min_length=32, strip_whitespace=True)]
