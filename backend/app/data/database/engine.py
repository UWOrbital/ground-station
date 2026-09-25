from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.env_settings.backend_config import settings


@lru_cache(maxsize=1)
def get_db_engine() -> AsyncEngine:
    """
    Creates (once) and returns the async database engine
    Cached so the connection pool is reused across requests

    :return: engine
    """
    return create_async_engine(
        settings.db.connection_string,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def get_db_session() -> AsyncSession:
    """
    Creates a new async session bound to the shared engine

    :return: session
    """
    engine = get_db_engine()
    # expire_on_commit=False keeps returned ORM objects usable after the session's
    # async context closes (async sessions can't lazily reload attributes afterwards).
    return AsyncSession(engine, expire_on_commit=False)
