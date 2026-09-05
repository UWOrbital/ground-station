import logging

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.aro.routes.auth import router as aro_auth_router
from app.api.v1.aro.routes.picture_requests import picture_requests_router
from app.api.v1.aro.routes.user import aro_user_router
from app.api.v1.mcc.routes.admin import admin_router
from app.api.v1.mcc.routes.aro_requests import aro_requests_router
from app.api.v1.mcc.routes.auth import mcc_auth_router
from app.api.v1.mcc.routes.commands import commands_router
from app.api.v1.mcc.routes.images import images_router
from app.api.v1.mcc.routes.main_commands import main_commands_router
from app.api.v1.mcc.routes.main_telemetry import main_telemetry_router
from app.api.v1.mcc.routes.sessions import comms_sessions_router
from app.api.v1.mcc.routes.status import status_router
from app.api.v1.mcc.routes.telemetry import telemetry_router
from app.api.v1.mcc.routes.users import mcc_users_router
from app.config.env_settings.backend_config import settings
from app.config.env_settings.cors_config import add_cors_middleware
from app.config.logger_middleware import LoggerMiddleware


def setup_routes(app: FastAPI) -> None:
    """Adds the routes to the app"""
    version_1 = "/api/v1"

    # ARO routes
    aro_prefix = f"{version_1}/aro"
    app.include_router(aro_user_router, prefix=f"{aro_prefix}/user")
    app.include_router(picture_requests_router, prefix=f"{aro_prefix}/requests")
    app.include_router(aro_auth_router, prefix=aro_prefix)

    # MCC routes
    mcc_prefix = f"{version_1}/mcc"
    app.include_router(commands_router, prefix=f"{mcc_prefix}/commands")
    app.include_router(telemetry_router, prefix=f"{mcc_prefix}/telemetry")
    app.include_router(aro_requests_router, prefix=f"{mcc_prefix}/requests")
    app.include_router(comms_sessions_router, prefix=f"{mcc_prefix}/sessions")
    app.include_router(main_commands_router, prefix=f"{mcc_prefix}/main-commands")
    app.include_router(main_telemetry_router, prefix=f"{mcc_prefix}/main-telemetry")
    app.include_router(mcc_auth_router, prefix=f"{mcc_prefix}/auth")
    app.include_router(mcc_users_router, prefix=f"{mcc_prefix}/users")
    app.include_router(admin_router, prefix=f"{mcc_prefix}/admin")
    app.include_router(status_router, prefix=f"{mcc_prefix}/status")
    app.include_router(images_router, prefix=f"{mcc_prefix}/images")


def setup_middlewares(app: FastAPI) -> None:
    """Adds the middlewares to the app"""
    add_cors_middleware(app)  # Cors middleware should be added first
    app.add_middleware(SessionMiddleware, secret_key=settings.auth.session_secret)
    app.add_middleware(
        LoggerMiddleware,
        excluded_endpoints=settings.logger.excluded_endpoints,
    )


def setup_logging() -> None:
    """Sets all logs from SQLAlchemy to the custom logger level VERBOSE"""
    verbose_level = 15  # DEBUG=10,  INFO=20
    logger.level("VERBOSE", no=verbose_level, color="<blue>")

    class SQLAlchemyHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            logger.log("VERBOSE", record.getMessage())

    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(verbose_level)
    sqlalchemy_logger.addHandler(SQLAlchemyHandler())
    sqlalchemy_logger.propagate = False
