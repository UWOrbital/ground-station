# types.py

from typing import Annotated

import phonenumbers
from pydantic.types import StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

NameField = Annotated[str, StringConstraints(min_length=1, max_length=67, strip_whitespace=True)]
FirstName = NameField
LastName = NameField

PhoneNumber = Annotated[
    str | phonenumbers.PhoneNumber, 
    PhoneNumberValidator(number_format="E164", default_region="CA")
]

CallSign = Annotated[
    str, 
    StringConstraints(min_length=1, max_length=100, to_upper=True, strip_whitespace=True)
] # TODO: stricten once i know what a callsign looks like

AccessToken = Annotated[
    str, 
    StringConstraints(min_length=32, strip_whitespace=True)
]