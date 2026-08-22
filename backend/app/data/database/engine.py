from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.env_settings.backend_config import settings
from app.data.models.aro_user_models import ARO_USER_SCHEMA_NAME
from app.data.models.main_models import MAIN_SCHEMA_NAME
from app.data.models.transactional_models import TRANSACTIONAL_SCHEMA_NAME


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


async def _create_schemas(session: AsyncSession) -> None:
    """
    Creates the schemas in the database.

    :param session: The session for which to create the schemas
    """
    connection = await session.connection()
    schemas = [MAIN_SCHEMA_NAME, TRANSACTIONAL_SCHEMA_NAME, ARO_USER_SCHEMA_NAME]
    for schema in schemas:
        # sqlalchemy doesn't check if the schema exists before attempting to create one
        await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    await session.commit()


'''Deprecated method to create tables, now handled by Alembic migrations
def _create_tables(session: Session) -> None:
    """
    Creates the tables.
    :warning: This assumes the relevant schemas were already created
    :param session: The session for which to create the schemas
    """
    metadatas = [MAIN_SCHEMA_METADATA, ARO_USER_SCHEMA_METADATA, TRANSACTIONAL_SCHEMA_METADATA]
    connection = session.connection()
    for metadata in metadatas:
        metadata.create_all(connection)
        connection.commit()
'''


async def setup_database(session: AsyncSession) -> None:
    """
    Creates the schemas for the session.
    Table creation is now handled by Alembic migrations

    :param session: The session for which to create the schemas
    """
    await _create_schemas(session)
