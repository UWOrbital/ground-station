from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.data.enums.transactional import SessionStatus
from app.data.models.main_models import MainTelemetry
from app.data.models.transactional_models import CommsSession, Packet, Telemetry
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    """TestClient with no auth overrides (telemetry endpoint is unauthenticated)."""
    yield TestClient(app)


@pytest.fixture(autouse=True)
def setup_main_telemetries(db_session):
    """Create MainTelemetry reference records needed for the join in get_all()."""
    telemetries = [
        MainTelemetry(id=1, name="Battery Voltage", format="float", data_size=4, total_size=4),
        MainTelemetry(id=2, name="Temperature", format="float", data_size=4, total_size=4),
        MainTelemetry(id=3, name="Solar Current", format="float", data_size=4, total_size=4),
    ]
    for t in telemetries:
        db_session.add(t)
    db_session.commit()


@pytest.fixture
def comms_session(db_session) -> CommsSession:
    """Create a test comms session."""
    session = CommsSession(
        id=uuid4(),
        start_time=datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC),
        end_time=datetime(2025, 6, 1, 12, 10, 0, tzinfo=UTC),
        status=SessionStatus.COMPLETED,
    )
    db_session.add(session)
    db_session.commit()
    return session


@pytest.fixture
def packet(db_session, comms_session: CommsSession) -> Packet:
    """Create a test packet linked to the comms session."""
    pkt = Packet(
        id=uuid4(),
        session_id=comms_session.id,
        raw_data=b"\x01\x02\x03",
        type_=2,  # DOWNLINK
        payload_data=b"\xab\xcd",
        offset=0,
    )
    db_session.add(pkt)
    db_session.commit()
    return pkt


# ---------------------------------------------Testing the GET / endpoint--------------------------------------------- #


def test_get_telemetry_duplicate_types(client: TestClient, db_session) -> None:
    """Test that multiple telemetry entries sharing the same type_ are all returned (no deduplication)."""
    t1 = Telemetry(
        id=uuid4(),
        type_=1,  # Battery Voltage
        value="3.7",
        timestamp=datetime(2025, 6, 1, 12, 0, 5, tzinfo=UTC),
    )
    t2 = Telemetry(
        id=uuid4(),
        type_=1,  # Battery Voltage (same type)
        value="3.8",
        timestamp=datetime(2025, 6, 1, 12, 0, 10, tzinfo=UTC),
    )
    db_session.add(t1)
    db_session.add(t2)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["type"] == "Battery Voltage"
    assert data[1]["type"] == "Battery Voltage"


def test_get_telemetry_value_none(client: TestClient, db_session) -> None:
    """Test that telemetry with value=None serializes as null in the response."""
    telemetry = Telemetry(
        id=uuid4(),
        type_=1,
        value=None,
        timestamp=datetime(2025, 6, 1, 12, 0, 5, tzinfo=UTC),
    )
    db_session.add(telemetry)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["value"] is None


def test_get_telemetry_success(client: TestClient, db_session) -> None:
    """Test successful retrieval of all telemetry entries."""
    telemetry = Telemetry(
        id=uuid4(),
        type_=1,  # Battery Voltage
        value="3.7",
        timestamp=datetime(2025, 6, 1, 12, 0, 5, tzinfo=UTC),
    )
    db_session.add(telemetry)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["type"] == "Battery Voltage"
    assert data[0]["value"] == "3.7"


def test_get_telemetry_empty(client: TestClient) -> None:
    """Test that an empty telemetry table returns an empty list."""
    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_get_telemetry_multiple_types(client: TestClient, db_session) -> None:
    """Test retrieving telemetry entries of different types."""
    t1 = Telemetry(
        id=uuid4(),
        type_=1,  # Battery Voltage
        value="3.7",
        timestamp=datetime(2025, 6, 1, 12, 0, 5, tzinfo=UTC),
    )
    t2 = Telemetry(
        id=uuid4(),
        type_=2,  # Temperature
        value="25.0",
        timestamp=datetime(2025, 6, 1, 12, 0, 10, tzinfo=UTC),
    )
    db_session.add(t1)
    db_session.add(t2)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    types = {entry["type"] for entry in data}
    assert types == {"Battery Voltage", "Temperature"}


def test_get_telemetry_with_packet_and_session(
    client: TestClient, db_session, comms_session: CommsSession, packet: Packet
) -> None:
    """Test that telemetry with a packet/session chain populates subrows."""
    telemetry = Telemetry(
        id=uuid4(),
        type_=1,
        value="3.7",
        packet_id=packet.id,
        timestamp=datetime(2025, 6, 1, 12, 0, 5, tzinfo=UTC),
    )
    db_session.add(telemetry)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    entry = data[0]
    assert entry["id"] == str(telemetry.id)
    assert entry["type"] == "Battery Voltage"
    assert entry["value"] == "3.7"
    # Subrows should contain packet/session info
    assert entry["subrows"] is not None
    assert len(entry["subrows"]) == 1
    sub = entry["subrows"][0]
    assert sub["packet"] == str(packet.id)
    assert sub["session"] == str(comms_session.id)
    assert sub["obc_state"] == "completed"


def test_get_telemetry_without_packet(client: TestClient, db_session) -> None:
    """Test that telemetry without a packet_id still returns (subrows use empty strings)."""
    telemetry = Telemetry(
        id=uuid4(),
        type_=3,  # Solar Current
        value="0.5",
        packet_id=None,
        timestamp=datetime(2025, 6, 1, 12, 0, 15, tzinfo=UTC),
    )
    db_session.add(telemetry)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    entry = data[0]
    assert entry["type"] == "Solar Current"
    assert entry["value"] == "0.5"
    # When packet_id is None, the left outer join yields None → subrows packet/session/obc_state become ""
    assert entry["subrows"] is not None
    assert len(entry["subrows"]) == 1
    sub = entry["subrows"][0]
    assert sub["packet"] == ""
    assert sub["session"] == ""
    assert sub["obc_state"] == ""


def test_get_telemetry_response_shape(client: TestClient, db_session) -> None:
    """Test that the response model shape is correct (id, type, value, timestamp, subrows)."""
    telemetry = Telemetry(
        id=uuid4(),
        type_=2,
        value="26.5",
        timestamp=datetime(2025, 6, 1, 12, 1, 0, tzinfo=UTC),
    )
    db_session.add(telemetry)
    db_session.commit()

    response = client.get("/api/v1/mcc/telemetry/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    entry = data[0]

    # Verify every expected key is present
    assert "id" in entry
    assert "type" in entry
    assert "value" in entry
    assert "timestamp" in entry
    assert "subrows" in entry

    # Verify types
    assert isinstance(entry["id"], str)
    assert isinstance(entry["type"], str)
    assert isinstance(entry["value"], str)
    assert isinstance(entry["timestamp"], str)
