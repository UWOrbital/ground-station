from uuid import UUID, uuid4

import pytest
from data.enums.transactional import CommandStatus
from data.tables.main_tables import MainCommand
from data.tables.mcc_user_tables import MCCUsers
from fastapi.testclient import TestClient
from main import app
from mcc_keycloak.client import keycloak


@pytest.fixture
def mcc_user(db_session):
    """Create a test MCC user in the database."""
    user = MCCUsers(id=uuid4(), email="test@uworbital.ca", phone_number=None)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def client(mcc_user):
    """TestClient with Keycloak auth dependencies overridden."""
    app.dependency_overrides[keycloak.get_current_user] = lambda: mcc_user
    app.dependency_overrides[keycloak.authenticate] = lambda: {}
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_main_commands(db_session):
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
    db_session.commit()


# ---------------------------------------------Testing the POST endpoint--------------------------------------------- #


def test_create_command_success(client: TestClient) -> None:
    """Test successful creation of a new command."""
    payload = {
        "type_": 1,
        "params": "test_params",
    }

    response = client.post("/api/v1/mcc/commands/", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert "id" in data
    assert data["status"] == CommandStatus.PENDING
    assert data["type_"] == 1
    assert data["params"] == "test_params"
    UUID(data["id"])


def test_create_command_duplicate(client: TestClient) -> None:
    """Test that creating a duplicate command is allowed and succeeds."""
    payload = {"type_": 2, "params": "duplicate_test"}

    response1 = client.post("/api/v1/mcc/commands/", json=payload)
    assert response1.status_code == 200
    command1_id = response1.json()["data"]["id"]

    response2 = client.post("/api/v1/mcc/commands/", json=payload)
    assert response2.status_code == 200
    command2_id = response2.json()["data"]["id"]

    assert command1_id != command2_id
    assert response2.json()["data"]["status"] == CommandStatus.PENDING
    assert response2.json()["data"]["type_"] == 2
    assert response2.json()["data"]["params"] == "duplicate_test"


def test_create_command_with_null_params(client: TestClient) -> None:
    """Test creating a command with null params."""
    payload = {"type_": 3, "params": None}

    response = client.post("/api/v1/mcc/commands/", json=payload)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["params"] is None
    assert data["status"] == CommandStatus.PENDING


def test_create_command_missing_type(client: TestClient) -> None:
    """Test that omitting the required type_ field returns a validation error."""
    payload = {"params": "some_params"}

    response = client.post("/api/v1/mcc/commands/", json=payload)

    assert response.status_code == 422


# ---------------------------------------------Testing the DELETE endpoint--------------------------------------------- #


def test_delete_command_success(client: TestClient) -> None:
    """Test successful deletion of an existing command."""
    create_response = client.post("/api/v1/mcc/commands/", json={"type_": 10})
    assert create_response.status_code == 200
    command_id = create_response.json()["data"]["id"]

    delete_response = client.delete(f"/api/v1/mcc/commands/{command_id}")

    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["message"] == f"Command {command_id} deleted successfully"


def test_delete_command_not_found(client: TestClient) -> None:
    """Test deleting a non-existent command returns 404."""
    non_existent_id = str(uuid4())

    response = client.delete(f"/api/v1/mcc/commands/{non_existent_id}")

    assert response.status_code == 404


def test_delete_command_invalid_uuid(client: TestClient) -> None:
    """Test deleting with an invalid UUID format returns 422."""
    response = client.delete("/api/v1/mcc/commands/not-a-valid-uuid")

    assert response.status_code == 422


def test_delete_command_twice(client: TestClient) -> None:
    """Test that deleting the same command twice fails on the second attempt."""
    create_response = client.post("/api/v1/mcc/commands/", json={"type_": 11})
    assert create_response.status_code == 200
    command_id = create_response.json()["data"]["id"]

    delete_response1 = client.delete(f"/api/v1/mcc/commands/{command_id}")
    assert delete_response1.status_code == 200

    delete_response2 = client.delete(f"/api/v1/mcc/commands/{command_id}")
    assert delete_response2.status_code == 404
