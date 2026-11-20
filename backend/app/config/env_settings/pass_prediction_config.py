from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PassPredictionConfig(BaseSettings):
    """
    Pydantic class for storing pass predictor settings
    """

    # Satellite to predict passes for (default: ISS)
    norad_cat_id: int = 25544

    # Ground station location. Default is UW E7
    station_latitude_deg: float = Field(default=43.4730, ge=-90, le=90)
    station_longitude_deg: float = Field(default=-80.5395, ge=-180, le=180)
    station_altitude_m: float = 372.0

    # Elevation cutoff for rise and set
    min_elevation_deg: float = Field(default=15.0, ge=0, lt=90)

    # Session padding around each pass. Before rise and after set
    pre_padding_s: int = Field(default=60, ge=0)
    post_padding_s: int = Field(default=60, ge=0)

    # How far ahead to predict
    window_days: int = Field(default=7, ge=1)

    # freeze_hours hours before a session starts, its times cannot change
    freeze_hours: float = Field(default=12.0, ge=0)

    # Minimum data between orbit data downloads. CelesTrak blocks clients that download
    # data more often than every 2 hours, so this cannot go below 2
    refresh_hours: float = Field(default=6.0, ge=2.0)

    celestrak_url: str = "https://celestrak.org/NORAD/elements/gp.php"
    request_timeout_s: float = Field(default=30.0, gt=0)

    model_config = SettingsConfigDict(
        env_prefix="PASS_PREDICTION_",
        env_file_encoding="utf-8",
        extra="ignore",
    )
