from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from app.data.enums.transactional import CommandStatus
from app.data.models.main_models import MainCommand
from app.data.models.mcc_user_models import MCCUsers
from app.data.models.transactional_models import CommsSession
from httpx import ASGITransport, AsyncClient
from main import app
from app.mcc_keycloak.client import keycloak


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


@pytest_asyncio.fixture
async def comms_session(db_session):
    """Create a test comms session in the database."""
    comms_session = CommsSession(
        id=uuid4(),
        start_time=datetime.now(UTC) + timedelta(minutes=30),
        end_time=datetime.now(UTC) + timedelta(minutes=40),
    )
    db_session.add(comms_session)
    await db_session.commit()
    return comms_session


@pytest_asyncio.fixture
async def locked_comms_session(db_session):
    """Create a test comms session currently within its lockout window."""
    comms_session = CommsSession(
        id=uuid4(),
        start_time=datetime.now(UTC) + timedelta(seconds=5),
        end_time=datetime.now(UTC) + timedelta(minutes=10),
    )
    db_session.add(comms_session)
    await db_session.commit()
    return comms_session


@pytest_asyncio.fixture(autouse=True)
async def setup_main_commands(db_session):
    """Setup MainCommand records needed for testing."""
    main_commands = [
        MainCommand(id=1, name="TestCmd1", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=2, name="TestCmd2", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=3, name="TestCmd3", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=4, name="TestCmd4", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=5, name="TestCmd5", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=6, name="TestCmd6", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=10, name="TestCmd10", params=None, format=None, data_size=4, total_size=4),
        MainCommand(id=11, name="TestCmd11", params=None, format=None, data_size=4, total_size=4),
    ]
    for cmd in main_commands:
        db_session.add(cmd)
    await db_session.commit()


# ---------------------------------------------Testing the POST endpoint--------------------------------------------- #


async def test_create_command_success(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test successful creation of a new command."""
    payload = {
        "type_": 1,
        "params": "test_params",
        "session_id": str(comms_session.id)
    }

    response = await client.post("/api/mcc/commands/", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert "id" in data
    assert data["status"] == CommandStatus.PENDING
    assert data["type_"] == 1
    assert data["params"] == "test_params"
    UUID(data["id"])


async def test_create_command_duplicate(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test that creating a duplicate command is allowed and succeeds."""
    payload = {
        "type_": 2,
        "params": "duplicate_test",
        "session_id": str(comms_session.id)
    }

    response1 = await client.post("/api/mcc/commands/", json=payload)
    assert response1.status_code == 200
    command1_id = response1.json()["data"]["id"]

    response2 = await client.post("/api/mcc/commands/", json=payload)
    assert response2.status_code == 200
    command2_id = response2.json()["data"]["id"]

    assert command1_id != command2_id
    assert response2.json()["data"]["status"] == CommandStatus.PENDING
    assert response2.json()["data"]["type_"] == 2
    assert response2.json()["data"]["params"] == "duplicate_test"


async def test_create_command_with_null_params(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test creating a command with null params."""
    payload = {
        "type_": 3,
        "params": None,
        "session_id": str(comms_session.id),
    }

    response = await client.post("/api/mcc/commands/", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["params"] is None
    assert data["status"] == CommandStatus.PENDING


async def test_create_command_missing_type(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test that omitting the required type_ field returns a validation error."""
    payload = {
        "params": "some_params",
        "session_id": str(comms_session.id),
    }

    response = await client.post("/api/mcc/commands/", json=payload)

    assert response.status_code == 422


async def test_create_command_missing_session(client: AsyncClient) -> None:
    """Test that omitting the required session_id returns a validation error."""
    payload = {
        "type_": 1,
        "params": "some_params",
    }

    response = await client.post("/api/mcc/commands/", json=payload)

    assert response.status_code == 422


async def test_create_command_session_locked_out(client: AsyncClient, locked_comms_session: CommsSession) -> None:
    """Test that creating a command for a session within its lockout window fails."""
    payload = {
        "type_": 1,
        "params": "test_params",
        "session_id": str(locked_comms_session.id),
    }

    response = await client.post("/api/mcc/commands/", json=payload)

    assert response.status_code == 409


async def test_create_command_session_not_found(client: AsyncClient) -> None:
    """Test that creating a command with a nonexistent session fails."""
    payload = {
        "type_": 1,
        "params": "test_params",
        "session_id": str(uuid4()),
    }

    response = await client.post("/api/mcc/commands/", json=payload)

    assert response.status_code == 404


# ---------------------------------------------Testing the PATCH endpoint--------------------------------------------- #


async def test_update_command_session_locked_out(client: AsyncClient, comms_session: CommsSession, db_session) -> None:
    """Test that updating a command whose session has since entered lockout fails."""
    create_response = await client.post("/api/mcc/commands/", json={"type_": 4, "session_id": str(comms_session.id)})
    assert create_response.status_code == 200
    command_id = create_response.json()["data"]["id"]

    comms_session.start_time = datetime.now(UTC) + timedelta(seconds=5)
    db_session.add(comms_session)
    await db_session.commit()

    response = await client.patch(f"/api/mcc/commands/{command_id}", json={"params": "updated"})

    assert response.status_code == 409


async def test_update_command_not_found(client: AsyncClient) -> None:
    """Test that updating a nonexistent command returns 404."""
    response = await client.patch(f"/api/mcc/commands/{uuid4()}", json={"params": "updated"})

    assert response.status_code == 404


# ---------------------------------------------Testing the DELETE endpoint--------------------------------------------- #


async def test_delete_command_success(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test successful deletion of an existing command."""
    create_response = await client.post("/api/mcc/commands/", json={"type_": 10, "session_id": str(comms_session.id)})
    assert create_response.status_code == 200
    command_id = create_response.json()["data"]["id"]

    delete_response = await client.delete(f"/api/mcc/commands/{command_id}")

    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["message"] == f"Command {command_id} deleted successfully"


async def test_delete_command_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent command returns 404."""
    non_existent_id = str(uuid4())

    response = await client.delete(f"/api/mcc/commands/{non_existent_id}")

    assert response.status_code == 404


async def test_delete_command_invalid_uuid(client: AsyncClient) -> None:
    """Test deleting with an invalid UUID format returns 422."""
    response = await client.delete("/api/mcc/commands/not-a-valid-uuid")

    assert response.status_code == 422


async def test_delete_command_twice(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test that deleting the same command twice fails on the second attempt."""
    create_response = await client.post("/api/mcc/commands/", json={"type_": 11, "session_id": str(comms_session.id)})
    assert create_response.status_code == 200
    command_id = create_response.json()["data"]["id"]

    delete_response1 = await client.delete(f"/api/mcc/commands/{command_id}")
    assert delete_response1.status_code == 200

    delete_response2 = await client.delete(f"/api/mcc/commands/{command_id}")
    assert delete_response2.status_code == 404


async def test_delete_command_session_locked_out(client: AsyncClient, comms_session: CommsSession, db_session) -> None:
    """Test that deleting a command whose session has since entered lockout fails."""
    create_response = await client.post("/api/mcc/commands/", json={"type_": 5, "session_id": str(comms_session.id)})
    assert create_response.status_code == 200
    command_id = create_response.json()["data"]["id"]

    comms_session.start_time = datetime.now(UTC) + timedelta(seconds=5)
    db_session.add(comms_session)
    await db_session.commit()

    response = await client.delete(f"/api/mcc/commands/{command_id}")

    assert response.status_code == 409


# ---------------------------------------------Testing the GET by session endpoint--------------------------------------------- #


async def test_get_commands_by_session(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test retrieving all commands for a given session."""
    await client.post("/api/mcc/commands/", json={"type_": 1, "session_id": str(comms_session.id)})
    await client.post("/api/mcc/commands/", json={"type_": 2, "session_id": str(comms_session.id)})

    response = await client.get(f"/api/mcc/commands/session/{comms_session.id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert all(cmd["session_id"] == str(comms_session.id) for cmd in data)


async def test_get_commands_by_session_empty(client: AsyncClient, comms_session: CommsSession) -> None:
    """Test that a session with no commands returns an empty list."""
    response = await client.get(f"/api/mcc/commands/session/{comms_session.id}")

    assert response.status_code == 200
    assert response.json()["data"] == []
