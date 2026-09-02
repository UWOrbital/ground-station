from decimal import Decimal

from pydantic import BaseModel, Field

from app.config.data_values import (
    COORDINATE_DECIMAL_NUMBER,
    LATITUDE_MAX_DIGIT_NUMBER,
    LONGITUDE_MAX_DIGIT_NUMBER,
)

# -----------------------------------------------------------------
# Picture Request Requests
# -----------------------------------------------------------------


class CreatePictureRequest(BaseModel):
    """
    Payload for creating a new ARO picture request.
    """

    latitude: Decimal = Field(max_digits=LATITUDE_MAX_DIGIT_NUMBER, decimal_places=COORDINATE_DECIMAL_NUMBER)
    longitude: Decimal = Field(max_digits=LONGITUDE_MAX_DIGIT_NUMBER, decimal_places=COORDINATE_DECIMAL_NUMBER)
