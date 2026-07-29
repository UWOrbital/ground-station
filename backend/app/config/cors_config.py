from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict


class CORSConfig(BaseSettings):
    """
    Pydantic class for storing CORS middleware configuration settings
    """

    model_config = SettingsConfigDict(env_prefix="CORS_")

    allow_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "https://app.uworbital.org",
    ]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


def add_cors_middleware(app: FastAPI) -> None:
    """
    Adds the cors middleware to the FastAPI app

    :param app: FastAPI app to add the middleware to
    """
    cors_settings = CORSConfig()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.allow_origins,
        allow_credentials=cors_settings.allow_credentials,
        allow_methods=cors_settings.allow_methods,
        allow_headers=cors_settings.allow_headers,
    )
