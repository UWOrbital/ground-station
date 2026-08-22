from uuid import UUID, uuid4

import pytest_asyncio
from app.data.models.main_models import MainCommand, MainTelemetry
from app.data.models.mcc_user_models import MCCUsers
from httpx import ASGITransport, AsyncClient
from main import app
from app.mcc_keycloak.client import keycloak

COMMANDS_PREFIX = "/api/v1/mcc/main-commands"
TELEMETRIES_PREFIX = "/api/v1/mcc/main-telemetry"


@pytest_asyncio.fixture
async def mcc_user(db_session):
    """Create a test MCC user in the database."""
    user = MCCUsers(id=uuid4(), email="test@uworbital.ca", phone_number=None)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def client(mcc_user):
    """AsyncClient with Keycloak auth dependencies overridden."""
    app.dependency_overrides[keycloak.get_current_user] = lambda: mcc_user
    app.dependency_overrides[keycloak.authenticate] = lambda: {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def setup_main_commands(db_session):
    """Setup MainCommand records needed for testing."""
    main_commands = [
        MainCommand(id=1, name="TestCmd1", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=2, name="TestCmd2", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=3, name="TestCmd3", params=None, format=None, data_size=4, total_size=4),
    ]
    for cmd in main_commands:
        db_session.add(cmd)
    await db_session.commit()


@pytest_asyncio.fixture(autouse=True)
async def setup_main_telemetries(db_session):
    """Setup MainCommand records needed for testing."""
    main_telemetries = [
        MainTelemetry(id=1, name="TestTlm1", format=None, data_size=4, total_size=4),
        MainTelemetry(id=2, name="TestTlm2", format=None, data_size=4, total_size=4),
        MainTelemetry(id=3, name="TestTlm3", format=None, data_size=4, total_size=4),
    ]
    for cmd in main_telemetries:
        db_session.add(cmd)
    await db_session.commit()

# --------------------------------------------- Testing Main Commands --------------------------------------------- #


async def test_get_commands_success(client: AsyncClient) -> None:
    """Test successful retrieval of all main commands."""
    response = await client.get(f"{COMMANDS_PREFIX}/")
    data = response.json()["data"]

    assert response.status_code == 200
    assert len(data) == 3
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[2]["id"] == 3
    assert data[0]["name"] == "TestCmd1"


async def test_get_command_by_id_success(client: AsyncClient) -> None:
    """Test successful retrieval of an existing command."""
    command_id = 1
    response = await client.get(f"{COMMANDS_PREFIX}/{command_id}")
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["name"] == "TestCmd1"


async def test_get_command_by_id_not_found(client: AsyncClient) -> None:
    """Test retrieving a non-existent command returns 404."""
    response = await client.get(f"{COMMANDS_PREFIX}/999")

    assert response.status_code == 404


async def test_get_command_by_invalid_id(client: AsyncClient) -> None:
    """Test retrieving a command using an invalid ID (non-integer) returns 422."""
    response = await client.get(f"{COMMANDS_PREFIX}/string")

    assert response.status_code == 422

# -------------------------------------------- Testing Main Telemetries -------------------------------------------- #


async def test_get_telemetries_success(client: AsyncClient) -> None:
    """Test successful retrieval of all main telemetries."""
    response = await client.get(f"{TELEMETRIES_PREFIX}/")
    data = response.json()["data"]

    assert response.status_code == 200
    assert len(data) == 3
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[2]["id"] == 3
    assert data[0]["name"] == "TestTlm1"


async def test_get_telemetry_by_id_success(client: AsyncClient) -> None:
    """Test successful retrieval of an existing telemetry."""
    telemetry_id = 1
    response = await client.get(f"{TELEMETRIES_PREFIX}/{telemetry_id}")
    data = response.json()["data"]

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["name"] == "TestTlm1"


async def test_get_telemetry_by_id_not_found(client: AsyncClient) -> None:
    """Test retrieving a non-existent telemetry returns 404."""
    response = await client.get(f"{TELEMETRIES_PREFIX}/999")

    assert response.status_code == 404


async def test_get_telemetry_by_invalid_id(client: AsyncClient) -> None:
    """Test retrieving a telemetry using an invalid ID (non-integer) returns 422."""
    response = await client.get(f"{TELEMETRIES_PREFIX}/string")

    assert response.status_code == 422
