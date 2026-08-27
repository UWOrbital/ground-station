from datetime import timedelta
from typing import Final

# TODO: Pull these from a config file?
CALL_SIGN_MIN_LENGTH: Final[int] = 5
CALL_SIGN_MAX_LENGTH: Final[int] = 6
DEFAULT_MAX_LENGTH: Final[int] = 255
PACKET_RAW_LENGTH: Final[int] = 255
PACKET_DATA_LENGTH: Final[int] = 223
EMAIL_MIN_LENGTH: Final[int] = 5
COORDINATE_DECIMAL_NUMBER: Final[int] = 3
LATITUDE_MAX_DIGIT_NUMBER: Final[int] = 5
LONGITUDE_MAX_DIGIT_NUMBER: Final[int] = 6
SESSION_LOCKOUT_SECONDS: Final[int] = 10
# Window after creation during which a PENDING ARO picture request may still be deleted.
PICTURE_REQUEST_DELETE_WINDOW: Final[timedelta] = timedelta(hours=24)
ACCESS_TOKEN_LIFETIME = timedelta(minutes=10)
REFRESH_TOKEN_LIFETIME = timedelta(days=14)
