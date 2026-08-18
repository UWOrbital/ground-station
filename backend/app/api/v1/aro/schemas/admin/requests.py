from pydantic import BaseModel
from app.api.v1.aro.schemas.types import CallSign, AROEmailField, FirstName, LastName, PhoneNumber

# -----------------------------------------------------------------
# Admin Requests
# -----------------------------------------------------------------


class UserRequest(BaseModel):
    """
    Model representing the user to be created directly by an operator.
    """

    call_sign: CallSign
    email: AROEmailField
    first_name: FirstName
    last_name: LastName
    phone_number: PhoneNumber
