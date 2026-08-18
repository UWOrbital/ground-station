from typing import Annotated

import phonenumbers
from pydantic import AfterValidator, EmailStr
from pydantic.types import StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

from app.config.data_values import CALL_SIGN_MAX_LENGTH, CALL_SIGN_MIN_LENGTH, DEFAULT_MAX_LENGTH, EMAIL_MIN_LENGTH


def normalize_email(email: str) -> str:
    """Enforce email length and lowercase the local part."""
    if len(email) < EMAIL_MIN_LENGTH:
        raise ValueError(f"First name cannot be shorter than {EMAIL_MIN_LENGTH} characters.")
    localpart, domain = email.split("@", 1)
    return f"{localpart.lower}@{domain}"


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

CallSign = Annotated[
    str,
    StringConstraints(
        min_length=CALL_SIGN_MIN_LENGTH, max_length=CALL_SIGN_MAX_LENGTH, to_upper=True, strip_whitespace=True
    ),
]  # TODO: stricten once i know what a callsign looks like

AccessToken = Annotated[str, StringConstraints(min_length=32, strip_whitespace=True)]
