import os
import subprocess
from datetime import datetime

os.environ.setdefault("ARO_AUTH_GOOGLE_CLIENT_ID", "dummy")
os.environ.setdefault("ARO_AUTH_GOOGLE_CLIENT_SECRET", "dummy")
os.environ.setdefault("ARO_AUTH_JWT_SECRET_KEY", "dummy")

os.environ.setdefault("GS_DATABASE_USER", "testuser")
os.environ.setdefault("GS_DATABASE_PASSWORD", "testpassword")
os.environ.setdefault("GS_DATABASE_LOCATION", "localhost")
os.environ.setdefault("GS_DATABASE_PORT", "5432")
os.environ.setdefault("GS_DATABASE_NAME", "testdb")

import pytest
from data.database.engine import setup_database
from data.tables.transactional_tables import CommsSession
from sqlalchemy import Engine, NullPool
from sqlmodel import Session, create_engine


@pytest.fixture
def db_engine(postgresql) -> Engine:
    """
    Creates a database engine fixture for the postgresql.
    This is a function level fixture.
    """
    connection = f"postgresql+psycopg://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    return create_engine(connection, echo=False, poolclass=NullPool)


@pytest.fixture
def db_session(db_engine: Engine) -> Session:
    """
    Creates a database session fixture for the postgresql.
    This is a function level fixture.
    """
    setup_session = Session(db_engine)
    setup_database(setup_session)

    # Run Alembic migrations to create tables
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["SQLALCHEMY_DATABASE_URL"] = str(db_engine.url)
    import sys
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=repo_root, env=env, check=True)
    setup_session.close()

    # Now yield a fresh session for the test
    with Session(db_engine) as session:
        yield session


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
