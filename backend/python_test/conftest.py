import os
import subprocess
from datetime import datetime

os.environ.setdefault("ARO_AUTH_GOOGLE_CLIENT_ID", "dummy")
os.environ.setdefault("ARO_AUTH_GOOGLE_CLIENT_SECRET", "dummy")
os.environ.setdefault("ARO_AUTH_JWT_SECRET_KEY", "dummy")

os.environ.setdefault("GS_DATABASE_USER", "testuser")
os.environ.setdefault("GS_DATABASE_PASSWORD", "testpassword")
os.environ.setdefault("GS_DATABASE_NAME", "testdb")

import pytest
from data.database.engine import setup_database
from data.tables.transactional_tables import CommsSession
from sqlalchemy import Engine, NullPool
from sqlmodel import Session, create_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgresql() -> PostgresContainer:
    """
    Creates a Postgres docker container for the test db.
    Also sets environment variables but they are not used directly as of now.
    Replaces pytest-postgresql fixture.
    """
    with PostgresContainer(
        image="postgres:16-alpine",
        username=os.environ.get("GS_DATABASE_USER"),
        password=os.environ.get("GS_DATABASE_PASSWORD"),
        dbname=os.environ.get("GS_DATABASE_NAME"),
        driver="psycopg"
    ) as pg:
        os.environ["GS_DATABASE_LOCATION"] = pg.get_container_host_ip()
        os.environ["GS_DATABASE_PORT"] = str(pg.get_exposed_port(5432))
        yield pg

@pytest.fixture(scope="session")
def db_engine(postgresql) -> Engine:
    """
    Creates a database engine fixture for the postgresql.
    """
    connection = postgresql.get_connection_url()
    return create_engine(connection, echo=False, poolclass=NullPool)

@pytest.fixture(scope="session", autouse=True)
def migrate_db(db_engine: Engine):
    """
    Runs Alembic migrations to create tables.
    """
    setup_session = Session(db_engine)
    setup_database(setup_session)

    # Run Alembic migrations to create tables
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    # Engine.url by default censors the password into "***" which breaks things
    env["SQLALCHEMY_DATABASE_URL"] = db_engine.url.render_as_string(hide_password=False)
    import sys
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=repo_root, env=env, check=True)
    setup_session.close()

@pytest.fixture
def db_session(db_engine: Engine) -> Session:
    """
    Creates a database session fixture for the postgresql.
    This is a function level fixture.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        # https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
        join_transaction_mode="create_savepoint",
    )

    # Now yield a fresh session for the test
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def default_start_time() -> datetime:
    return datetime(2025, 1, 1, 12, 25, 38)


@pytest.fixture
def default_comms_session(default_start_time: datetime) -> CommsSession:
    """
    Creates the comms session
    This is a function level fixture.
    """
    comms_session_item = CommsSession(start_time=default_start_time)
    return comms_session_item


@pytest.fixture(autouse=True)
def test_get_db_session(monkeypatch, db_session: Session):
    from contextlib import contextmanager

    @contextmanager
    def _get_db_session():
        yield db_session

    monkeypatch.setattr(
        "data.data_wrappers.abstract_wrapper.get_db_session",
        _get_db_session,
        raising=True,
    )
