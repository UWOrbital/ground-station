# types.py

from typing import Annotated

import phonenumbers
from pydantic.types import StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

from app.config.data_values import (
    CALL_SIGN_MAX_LENGTH,
    CALL_SIGN_MIN_LENGTH,
    DEFAULT_MAX_LENGTH,
)

NameField = Annotated[
    str, StringConstraints(
        min_length=1,
        max_length=DEFAULT_MAX_LENGTH,
        strip_whitespace=True
    )
]
FirstName = NameField
LastName = NameField

PhoneNumber = Annotated[
    str | phonenumbers.PhoneNumber,
    PhoneNumberValidator(
        number_format="E164",
        default_region="CA"
    )
]

CallSign = Annotated[
    str, StringConstraints(
        min_length=CALL_SIGN_MIN_LENGTH,
        max_length=CALL_SIGN_MAX_LENGTH,
        to_upper=True,
        strip_whitespace=True
    )
]  # TODO: stricten once i know what a callsign looks like

AccessToken = Annotated[
    str, StringConstraints(
        min_length=32,
        strip_whitespace=True
    )
]
