import os
import subprocess
import sys
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

os.environ.setdefault("ARO_AUTH_JWT_SECRET", "dummy" * 8)
os.environ.setdefault("ARO_AUTH_SESSION_SECRET", "dummy" * 8)

os.environ.setdefault("GS_DATABASE_USER", "testuser")
os.environ.setdefault("GS_DATABASE_PASSWORD", "testpassword")
os.environ.setdefault("GS_DATABASE_NAME", "testdb")

os.environ.setdefault("KEYCLOAK_URL", "http://localhost:8080")
os.environ.setdefault("KEYCLOAK_CLIENT_SECRET", "dummy")

import pytest
import pytest_asyncio
from app.data.enums.transactional import SessionSource
from app.data.models.transactional_models import OrbitElement, Session
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
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
        driver="asyncpg",
    ) as pg:
        os.environ["GS_DATABASE_LOCATION"] = pg.get_container_host_ip()
        os.environ["GS_DATABASE_PORT"] = str(pg.get_exposed_port(5432))
        yield pg


@pytest_asyncio.fixture(scope="session")
async def db_engine(postgresql: PostgresContainer) -> AsyncGenerator[AsyncEngine, None]:
    """
    Creates an async database engine fixture for the postgresql container.
    """
    connection = postgresql.get_connection_url()  # postgresql+asyncpg://...
    engine = create_async_engine(connection, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def migrate_db(db_engine: AsyncEngine) -> None:
    """
    Runs Alembic migrations to create the test database schema.
    """

    # Alembic is the only mechanism that creates the test database schema.
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = os.environ.copy()
    # Engine.url by default censors the password into "***" which breaks things.
    env["SQLALCHEMY_DATABASE_URL"] = db_engine.url.render_as_string(hide_password=False)
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=repo_root, env=env, check=True)


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Creates an async database session fixture for the postgresql.
    This is a function level fixture. Each test runs inside an outer transaction
    that is rolled back on teardown, so tests never persist to the shared db.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(
        bind=connection,
        # https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
        join_transaction_mode="create_savepoint",
        # Match the production session (see engine.get_db_session): keep attributes
        # populated after commit so tests can read them without a lazy async reload.
        expire_on_commit=False,
    )

    # Now yield a fresh session for the test
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
def default_start_time() -> datetime:
    return datetime(2025, 1, 1, 12, 25, 38, tzinfo=UTC)


@pytest.fixture
def default_session(default_start_time: datetime) -> Session:
    """
    Creates the session
    This is a function level fixture.
    """
    session_item = Session(start_time=default_start_time, end_time=default_start_time + timedelta(minutes=5))
    return session_item


ISS_NORAD_CAT_ID = 25544
# Trimmed CelesTrak JSON OMM record
# Only stored as JSONB, not parsed by the backend
ISS_OMM: dict[str, Any] = {
    "OBJECT_NAME": "ISS (ZARYA)",
    "OBJECT_ID": "1998-067A",
    "EPOCH": "2026-11-19T04:55:07.676544",
    "NORAD_CAT_ID": ISS_NORAD_CAT_ID,
}


@pytest_asyncio.fixture
async def orbit_element(db_session: AsyncSession) -> OrbitElement:
    """Insert and return a minimal orbit element row for the ISS.

    :param db_session: test database session.
    :return: the persisted OrbitElement.
    """
    element = OrbitElement(
        norad_cat_id=ISS_NORAD_CAT_ID, epoch=datetime(2026, 11, 19, 4, 55, 7, 676544, tzinfo=UTC), omm=ISS_OMM
    )
    db_session.add(element)
    await db_session.commit()
    return element


@pytest.fixture
def make_predicted_session(orbit_element: OrbitElement) -> Callable[..., Session]:
    """Return a factory that builds valid, unsaved predicted sessions.

    :param orbit_element: orbit element the predictions reference
    :return: factory taking the padded window start plus field overrides.
    """

    def _make(start: datetime, **overrides: Any) -> Session:
        """Build a predicted session starting at the given padded start time.

        :param start: padded window start.
        :param overrides: Session fields to replace in the default pass.
        :return: an unsaved Session.
        """
        rise_time = start + timedelta(seconds=60)
        set_time = rise_time + timedelta(minutes=8)
        fields: dict[str, Any] = {
            "start_time": start,
            "end_time": set_time + timedelta(seconds=60),
            "source": SessionSource.PREDICTED,
            "rise_time": rise_time,
            "peak_time": rise_time + timedelta(minutes=4),
            "set_time": set_time,
            "min_elevation_deg": 15.0,
            "max_elevation_deg": 63.2,
            "rise_azimuth_deg": 215.0,
            "set_azimuth_deg": 40.5,
            "orbit_element_id": orbit_element.id,
        }
        fields.update(overrides)
        return Session(**fields)

    return _make


@pytest.fixture(autouse=True)
def test_get_db_session(monkeypatch, db_session: AsyncSession):
    @asynccontextmanager
    async def _get_db_session():
        yield db_session

    monkeypatch.setattr(
        "app.data.repositories.abstract_repository.get_db_session",
        _get_db_session,
        raising=True,
    )
    monkeypatch.setattr(
        "app.data.repositories.repositories.get_db_session",
        _get_db_session,
        raising=True,
    )
