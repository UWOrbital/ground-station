from functools import lru_cache

from config.config import settings
from sqlalchemy import Engine
from sqlmodel import Session, create_engine, text

from data.tables.aro_user_tables import ARO_USER_SCHEMA_NAME
from data.tables.main_tables import MAIN_SCHEMA_NAME
from data.tables.transactional_tables import TRANSACTIONAL_SCHEMA_NAME


@lru_cache(maxsize=1)
def get_db_engine() -> Engine:
    """
    Creates (once) and returns the database engine
    Cached so the connection pool is reused across requests

    :return: engine
    """
    return create_engine(
        settings.db.connection_string,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def get_db_session() -> Session:
    """
    Creates a new session bound to the shared engine

    :return: session
    """
    engine = get_db_engine()
    return Session(engine)


def _create_schemas(session: Session) -> None:
    """
    Creates the schemas in the database.

    :param session: The session for which to create the schemas
    """
    connection = session.connection()
    schemas = [MAIN_SCHEMA_NAME, TRANSACTIONAL_SCHEMA_NAME, ARO_USER_SCHEMA_NAME]
    for schema in schemas:
        # sqlalchemy doesn't check if the schema exists before attempting to create one
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    connection.commit()


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


def setup_database(session: Session) -> None:
    """
    Creates the schemas for the session.
    Table creation is now handled by Alembic migrations

    :param session: The session for which to create the schemas
    """
    _create_schemas(session)
