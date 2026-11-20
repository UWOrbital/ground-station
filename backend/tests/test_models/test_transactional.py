from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from app.data.enums.aro_requests import ARORequestStatus
from app.data.enums.transactional import (
    CommandStatus,
    MainPacketType,
    OrbitElementSource,
    SessionSource,
    SessionStatus,
)
from app.data.models.aro_user_models import AROUsers
from app.data.models.main_models import MainCommand, MainTelemetry
from app.data.models.transactional_models import (
    ARORequest,
    Command,
    Image,
    OrbitElement,
    Packet,
    Session,
    Telemetry,
)
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def test_commands_basic(db_session: AsyncSession, default_session: Session):
    # Setup the session
    db_session.add(default_session)
    await db_session.commit()

    # Setup the MainCommand table
    main_command1 = MainCommand(id=1, name="Test 1", data_size=1, total_size=2, format="int", params="time")
    db_session.add(main_command1)
    await db_session.commit()

    # Make sure that the main command was successfully inserted into the db
    main_commands_query = select(MainCommand)
    main_commands_items = (await db_session.exec(main_commands_query)).all()
    assert len(main_commands_items) == 1

    # Test the commands table
    id = uuid4()
    command1 = Command(id=id, type_=main_command1.id, params="1234567", session_id=default_session.id)
    db_session.add(command1)
    await db_session.commit()

    commands_query = select(Command)
    commands_items = (await db_session.exec(commands_query)).all()

    assert len(commands_items) == 1
    returned_item1 = commands_items[0]
    assert returned_item1.id == id
    assert returned_item1.type_ == 1
    assert returned_item1.params == "1234567"
    assert returned_item1.status == CommandStatus.PENDING

    # Start the delete portion of the test
    await db_session.delete(main_command1)
    main_commands_items = (await db_session.exec(main_commands_query)).all()
    assert len(main_commands_items) == 0

    # Make sure it cascades
    commands_items = (await db_session.exec(commands_query)).all()
    assert len(commands_items) == 0


async def test_telemetry_basic(db_session: AsyncSession):
    # Setup the MainTelemetry table
    main_telemetry = MainTelemetry(id=1, name="Test 1", data_size=1, total_size=2, format="int 7 bytes")
    db_session.add(main_telemetry)
    await db_session.commit()

    # Make sure that the main telemetry was successfully inserted into the db
    main_telemetry_query = select(MainTelemetry)
    main_telemetry_items = (await db_session.exec(main_telemetry_query)).all()
    assert len(main_telemetry_items) == 1

    # Test the telemetry table
    id = uuid4()
    telemetry1 = Telemetry(id=id, type_=main_telemetry.id)
    db_session.add(telemetry1)
    await db_session.commit()

    telemetry_query = select(Telemetry)
    telemetry_items = (await db_session.exec(telemetry_query)).all()

    assert len(telemetry_items) == 1
    returned_item1 = telemetry_items[0]
    assert returned_item1.id == id
    assert returned_item1.type_ == 1
    assert returned_item1.value is None

    # Start the delete portion of the test
    await db_session.delete(main_telemetry)
    main_telemetry_items = (await db_session.exec(main_telemetry_query)).all()
    assert len(main_telemetry_items) == 0

    # Make sure it cascades
    commands_items = (await db_session.exec(telemetry_query)).all()
    assert len(commands_items) == 0


async def test_session_basic(
    db_session: AsyncSession, default_start_time: datetime, default_session: Session
):
    # Setup
    id = default_session.id  # sqlmodel generates the uuid before it's sent to the db

    # Db actions
    db_session.add(default_session)
    await db_session.commit()
    session_query = select(Session)
    session_items = (await db_session.exec(session_query)).all()

    # Assertions
    assert len(session_items) == 1
    returned_item1 = session_items[0]
    assert returned_item1.id == id
    assert returned_item1.start_time == default_start_time
    assert returned_item1.end_time == default_start_time + timedelta(minutes=5)
    assert returned_item1.status == SessionStatus.PENDING
    # Sessions default to manual, which have no pass data
    assert returned_item1.source == SessionSource.MANUAL
    assert returned_item1.rise_time is None
    assert returned_item1.peak_time is None
    assert returned_item1.set_time is None
    assert returned_item1.min_elevation_deg is None
    assert returned_item1.max_elevation_deg is None
    assert returned_item1.rise_azimuth_deg is None
    assert returned_item1.set_azimuth_deg is None
    assert returned_item1.orbit_element_id is None
    assert returned_item1.orphaned_at is None


# -------------------------------------------Session pass data and constraints------------------------------------------- #


async def _assert_rejected(db_session: AsyncSession, session: Session, constraint: str) -> None:
    """Assert that flushing the session violates the constraint, then reset the transaction.

    :param db_session: test database session
    :param session: unsaved session expected to be rejected
    :param constraint: name of the constraint expected in the database error
    """
    db_session.add(session)
    with pytest.raises(IntegrityError, match=constraint):
        await db_session.flush()
    await db_session.rollback()


async def test_predicted_session_valid(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    orbit_element: OrbitElement,
) -> None:
    session = make_predicted_session(default_start_time)
    db_session.add(session)
    await db_session.commit()

    returned = (await db_session.exec(select(Session).where(Session.id == session.id))).one()
    assert returned.source == SessionSource.PREDICTED
    assert returned.rise_time == default_start_time + timedelta(seconds=60)
    assert returned.min_elevation_deg == 15.0
    assert returned.max_elevation_deg == 63.2
    assert returned.orbit_element_id == orbit_element.id


async def test_predicted_session_zero_padding_allowed(
    db_session: AsyncSession, default_start_time: datetime, make_predicted_session: Callable[..., Session]
) -> None:
    session = make_predicted_session(default_start_time)
    session.start_time = session.rise_time
    session.end_time = session.set_time
    db_session.add(session)
    await db_session.commit()


async def test_predicted_session_missing_fields(db_session: AsyncSession, default_start_time: datetime) -> None:
    """A predicted session without pass data is rejected."""
    session = Session(
        start_time=default_start_time,
        end_time=default_start_time + timedelta(minutes=10),
        source=SessionSource.PREDICTED,
    )
    await _assert_rejected(db_session, session, "ck_sessions_predicted_fields")


async def test_predicted_session_missing_orbit_element(
    db_session: AsyncSession, default_start_time: datetime, make_predicted_session: Callable[..., Session]
) -> None:
    """A predicted session must reference the orbit elements it was computed from."""
    session = make_predicted_session(default_start_time, orbit_element_id=None)
    await _assert_rejected(db_session, session, "ck_sessions_predicted_fields")


async def test_session_start_equals_end(db_session: AsyncSession, default_start_time: datetime) -> None:
    """A session window must have a positive length."""
    session = Session(start_time=default_start_time, end_time=default_start_time)
    await _assert_rejected(db_session, session, "ck_sessions_start_before_end")


async def test_session_end_before_start(db_session: AsyncSession, default_start_time: datetime) -> None:
    """A session cannot end before it starts."""
    session = Session(start_time=default_start_time, end_time=default_start_time - timedelta(minutes=1))
    await _assert_rejected(db_session, session, "ck_sessions_start_before_end")


@pytest.mark.parametrize(
    ("peak_offset", "set_offset"),
    [
        (timedelta(0), timedelta(minutes=8)),  # rise == peak
        (timedelta(minutes=8), timedelta(minutes=8)),  # peak == set
        (timedelta(minutes=9), timedelta(minutes=8)),  # peak after set
    ],
)
async def test_session_pass_order(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    peak_offset: timedelta,
    set_offset: timedelta,
) -> None:
    """Rise, peak and set must be strictly increasing.

    :param peak_offset: peak time relative to rise
    :param set_offset: set time relative to rise
    """
    rise = default_start_time + timedelta(seconds=60)
    session = make_predicted_session(
        default_start_time,
        peak_time=rise + peak_offset,
        set_time=rise + set_offset,
        end_time=rise + timedelta(minutes=10),
    )
    await _assert_rejected(db_session, session, "ck_sessions_pass_order")


async def test_session_padding_inside_pass_start(
    db_session: AsyncSession, default_start_time: datetime, make_predicted_session: Callable[..., Session]
) -> None:
    """The padded start cannot fall after rise."""
    session = make_predicted_session(default_start_time)
    assert session.rise_time is not None
    session.start_time = session.rise_time + timedelta(seconds=1)
    await _assert_rejected(db_session, session, "ck_sessions_padding_outside_pass")


async def test_session_padding_inside_pass_end(
    db_session: AsyncSession, default_start_time: datetime, make_predicted_session: Callable[..., Session]
) -> None:
    """The padded end cannot fall before set."""
    session = make_predicted_session(default_start_time)
    assert session.set_time is not None
    session.end_time = session.set_time - timedelta(seconds=1)
    await _assert_rejected(db_session, session, "ck_sessions_padding_outside_pass")


@pytest.mark.parametrize("max_elevation", [15.0, 14.9])
async def test_session_peak_not_above_cutoff(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    max_elevation: float,
) -> None:
    """A pass whose peak lower than or at the minimum elevation is not a pass.

    :param max_elevation: peak elevation at or below the 15 degree cutoff
    """
    session = make_predicted_session(default_start_time, max_elevation_deg=max_elevation)
    await _assert_rejected(db_session, session, "ck_sessions_peak_above_cutoff")


@pytest.mark.parametrize("min_elevation", [-1.0, 90.1])
async def test_session_min_elevation_out_of_range(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    min_elevation: float,
) -> None:
    """The elevation cutoff must be between 0 and 90 degrees.

    :param min_elevation: cutoff outside [0, 90]
    """
    session = make_predicted_session(default_start_time, min_elevation_deg=min_elevation)
    await _assert_rejected(db_session, session, "ck_sessions_min_elevation_range")


@pytest.mark.parametrize("max_elevation", [-1.0, 90.1])
async def test_session_max_elevation_out_of_range(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    max_elevation: float,
) -> None:
    """The peak elevation must be between 0 and 90 degrees.

    :param max_elevation: cutoff outside [0, 90]
    """
    session = make_predicted_session(default_start_time, max_elevation_deg=max_elevation)
    await _assert_rejected(db_session, session, "ck_sessions_max_elevation_range")


async def test_session_elevation_bounds_inclusive(
    db_session: AsyncSession, default_start_time: datetime, make_predicted_session: Callable[..., Session]
) -> None:
    """A 0 degree cutoff and a 90 degree peak are both valid."""
    session = make_predicted_session(default_start_time, min_elevation_deg=0.0, max_elevation_deg=90.0)
    db_session.add(session)
    await db_session.commit()


@pytest.mark.parametrize(
    ("field", "value"),
    [("rise_azimuth_deg", 360.0), ("rise_azimuth_deg", -0.5), ("set_azimuth_deg", 360.0), ("set_azimuth_deg", -1.0)],
)
async def test_session_azimuth_out_of_range(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    field: str,
    value: float,
) -> None:
    """Azimuths must be in [0, 360).

    :param field: azimuth field to set out of range
    :param value: out-of-range azimuth
    """
    session = make_predicted_session(default_start_time, **{field: value})
    await _assert_rejected(db_session, session, "ck_sessions_azimuth_range")


async def test_manual_session_skips_pass_checks(db_session: AsyncSession, default_start_time: datetime) -> None:
    session = Session(
        start_time=default_start_time,
        end_time=default_start_time + timedelta(minutes=1),
        source=SessionSource.MANUAL,
    )
    db_session.add(session)
    await db_session.commit()


# ------------------------------------------------------Orbit elements------------------------------------------------------ #


async def test_orbit_element_basic(db_session: AsyncSession, orbit_element: OrbitElement) -> None:
    """Orbit elements default to CelesTrak, get a created_at, and keep the OMM JSON."""
    returned = (await db_session.exec(select(OrbitElement).where(OrbitElement.id == orbit_element.id))).one()
    assert returned.norad_cat_id == 25544
    assert returned.source == OrbitElementSource.CELESTRAK
    assert returned.omm["OBJECT_NAME"] == "ISS (ZARYA)"
    assert returned.omm["NORAD_CAT_ID"] == 25544
    assert returned.created_at is not None


async def test_orbit_element_duplicate_epoch(db_session: AsyncSession, orbit_element: OrbitElement) -> None:
    """The same satellite cannot have two element sets with the same epoch."""
    duplicate = OrbitElement(
        norad_cat_id=orbit_element.norad_cat_id,
        epoch=orbit_element.epoch,
        omm=orbit_element.omm,
        source=OrbitElementSource.MANUAL,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError, match="uq_orbit_elements_norad_cat_id_epoch"):
        await db_session.flush()
    await db_session.rollback()


async def test_orbit_element_same_epoch_other_satellite(
    db_session: AsyncSession, orbit_element: OrbitElement
) -> None:
    """Another catalog number can share the epoch."""
    other = OrbitElement(norad_cat_id=99999, epoch=orbit_element.epoch, omm={"NORAD_CAT_ID": 99999})
    db_session.add(other)
    await db_session.commit()


async def test_orbit_element_in_use_cannot_be_deleted(
    db_session: AsyncSession,
    default_start_time: datetime,
    make_predicted_session: Callable[..., Session],
    orbit_element: OrbitElement,
) -> None:
    db_session.add(make_predicted_session(default_start_time))
    await db_session.commit()

    await db_session.delete(orbit_element)
    with pytest.raises(IntegrityError, match="sessions_orbit_element_id_fkey"):
        await db_session.flush()
    await db_session.rollback()


async def test_orbit_element_unused_can_be_deleted(db_session: AsyncSession, orbit_element: OrbitElement) -> None:
    await db_session.delete(orbit_element)
    await db_session.commit()
    assert (await db_session.exec(select(OrbitElement))).all() == []


async def test_packet_basic(db_session: AsyncSession, default_session: Session):
    # Setup the session table
    db_session.add(default_session)
    await db_session.commit()
    session_query = select(Session)
    session_items = (await db_session.exec(session_query)).all()
    assert len(session_items) == 1  # Make sure it was inserted into the db
    id = session_items[0].id

    # Test the packet
    # TODO: Move this data to a fixture
    packet = Packet(
        session_id=id,
        raw_data=b"Hello world",
        type_=MainPacketType.UPLINK,
        payload_data=b"Hello world. Extra info.",
        offset=1,
    )
    db_session.add(packet)
    await db_session.commit()
    packet_query = select(Packet)
    packet_items = (await db_session.exec(packet_query)).all()

    assert len(packet_items) == 1
    returned_items1 = packet_items[0]
    assert returned_items1.type_ == MainPacketType.UPLINK
    assert returned_items1.raw_data == b"Hello world"
    assert returned_items1.payload_data == b"Hello world. Extra info."
    assert returned_items1.offset == 1

    # Test the delete cascading
    await db_session.delete(default_session)
    await db_session.commit()
    session_items = (await db_session.exec(session_query)).all()
    assert len(session_items) == 0

    packet_items = (await db_session.exec(packet_query)).all()
    assert len(packet_items) == 0


async def test_aro_requests_no_packet(db_session: AsyncSession):
    # Setup the database
    user_data = AROUsers(call_sign="123456", email="bob@test.com", first_name="Bob", phone_number="123456789")
    db_session.add(user_data)
    await db_session.commit()
    user_data_query = select(AROUsers)
    user_data_items = (await db_session.exec(user_data_query)).all()
    assert len(user_data_items) == 1

    # Insert the aro request
    aro_request = ARORequest(aro_id=user_data.id, latitude=Decimal(30), longitude=Decimal(40))
    db_session.add(aro_request)
    await db_session.commit()

    aro_request_query = select(ARORequest)
    aro_request_items = (await db_session.exec(aro_request_query)).all()
    assert len(aro_request_items) == 1
    data_returned1 = aro_request_items[0]
    assert data_returned1.aro_id == user_data.id
    assert data_returned1.status == ARORequestStatus.PENDING
    assert data_returned1.latitude == Decimal(30)
    assert data_returned1.longitude == Decimal(40)


async def _make_packet(db_session: AsyncSession, default_session: Session) -> Packet:
    """Persist a session and a downlink packet, returning the packet."""
    db_session.add(default_session)
    await db_session.commit()

    packet = Packet(
        session_id=default_session.id,
        raw_data=b"Hello world",
        type_=MainPacketType.DOWNLINK,
        payload_data=b"Hello world. Extra info.",
        offset=1,
    )
    db_session.add(packet)
    await db_session.commit()
    return packet


async def test_packet_subtype_defaults_none(db_session: AsyncSession, default_session: Session):
    # Setup
    packet = await _make_packet(db_session, default_session)

    # subtype is optional and defaults to None
    returned = (await db_session.exec(select(Packet).where(Packet.id == packet.id))).one()
    assert returned.subtype is None

    # but can be set
    returned.subtype = "image-chunk"
    db_session.add(returned)
    await db_session.commit()
    refetched = (await db_session.exec(select(Packet).where(Packet.id == packet.id))).one()
    assert refetched.subtype == "image-chunk"


async def test_telemetry_packet_link(db_session: AsyncSession, default_session: Session):
    # Setup the database
    main_telemetry = MainTelemetry(id=1, name="Test 1", data_size=1, total_size=2, format="int 7 bytes")
    db_session.add(main_telemetry)
    await db_session.commit()

    packet = await _make_packet(db_session, default_session)

    # Telemetry now links directly to a packet with a sequence index and a timestamp
    id = uuid4()
    telemetry = Telemetry(id=id, type_=main_telemetry.id, packet_id=packet.id, sequence_index=2)
    db_session.add(telemetry)
    await db_session.commit()

    returned = (await db_session.exec(select(Telemetry).where(Telemetry.id == id))).one()
    assert returned.packet_id == packet.id
    assert returned.sequence_index == 2
    assert returned.timestamp is not None

    # Deleting the packet sets the link to null but keeps the telemetry row
    await db_session.delete(packet)
    await db_session.commit()
    db_session.expire_all()
    survivor = (await db_session.exec(select(Telemetry).where(Telemetry.id == id))).one()
    assert survivor.packet_id is None


async def test_commands_packet_link(db_session: AsyncSession, default_session: Session):
    # Setup the database
    main_command = MainCommand(id=1, name="Test 1", data_size=1, total_size=2, format="int", params="time")
    db_session.add(main_command)
    await db_session.commit()

    packet = await _make_packet(db_session, default_session)

    # Commands now link directly to a packet with a sequence index
    id = uuid4()
    command = Command(
        id=id, type_=main_command.id, packet_id=packet.id, sequence_index=0, session_id=default_session.id
    )
    db_session.add(command)
    await db_session.commit()

    returned = (await db_session.exec(select(Command).where(Command.id == id))).one()
    assert returned.packet_id == packet.id
    assert returned.sequence_index == 0
    assert returned.status == CommandStatus.PENDING

    # Deleting the packet sets the link to null but keeps the command row
    await db_session.delete(packet)
    await db_session.commit()
    db_session.expire_all()
    survivor = (await db_session.exec(select(Command).where(Command.id == id))).one()
    assert survivor.packet_id is None


async def test_command_response_defaults_none(db_session: AsyncSession, default_session: Session):
    # Setup the database
    main_command = MainCommand(id=1, name="Test 1", data_size=1, total_size=2, format="int", params="time")
    db_session.add(main_command)
    await db_session.commit()
    db_session.add(default_session)
    await db_session.commit()

    # A command is queued before the OBC has replied, so response starts empty
    id = uuid4()
    command = Command(id=id, type_=main_command.id, params="1234567", session_id=default_session.id)
    db_session.add(command)
    await db_session.commit()

    returned = (await db_session.exec(select(Command).where(Command.id == id))).one()
    assert returned.response is None

    # The response is filled in once the downlink carrying it is decoded
    returned.response = "ACK"
    db_session.add(returned)
    await db_session.commit()
    refetched = (await db_session.exec(select(Command).where(Command.id == id))).one()
    assert refetched.response == "ACK"


async def _make_aro_request(db_session: AsyncSession) -> ARORequest:
    """Persist an ARO user and a picture request, returning the request."""
    user_data = AROUsers(call_sign="123456", email="bob@test.com", first_name="Bob", phone_number="123456789")
    db_session.add(user_data)
    await db_session.commit()

    aro_request = ARORequest(aro_id=user_data.id, latitude=Decimal(30), longitude=Decimal(40))
    db_session.add(aro_request)
    await db_session.commit()
    return aro_request


async def test_image_basic(db_session: AsyncSession, default_session: Session):
    # Setup the database
    packet = await _make_packet(db_session, default_session)
    aro_request = await _make_aro_request(db_session)

    # Test the images table
    id = uuid4()
    image = Image(id=id, data="base64-encoded-pixels", packet_id=packet.id, aro_id=aro_request.id)
    db_session.add(image)
    await db_session.commit()

    returned = (await db_session.exec(select(Image).where(Image.id == id))).one()
    assert returned.data == "base64-encoded-pixels"
    assert returned.packet_id == packet.id
    assert returned.aro_id == aro_request.id


async def test_image_links_default_none(db_session: AsyncSession):
    # An image can be stored before it is matched to a packet or a request
    id = uuid4()
    image = Image(id=id, data="base64-encoded-pixels")
    db_session.add(image)
    await db_session.commit()

    returned = (await db_session.exec(select(Image).where(Image.id == id))).one()
    assert returned.packet_id is None
    assert returned.aro_id is None


async def test_image_survives_packet_and_request_delete(db_session: AsyncSession, default_session: Session):
    # Setup the database
    packet = await _make_packet(db_session, default_session)
    aro_request = await _make_aro_request(db_session)

    id = uuid4()
    image = Image(id=id, data="base64-encoded-pixels", packet_id=packet.id, aro_id=aro_request.id)
    db_session.add(image)
    await db_session.commit()

    # Deleting either link sets it to null but keeps the downlinked image itself
    await db_session.delete(packet)
    await db_session.delete(aro_request)
    await db_session.commit()
    db_session.expire_all()

    survivor = (await db_session.exec(select(Image).where(Image.id == id))).one()
    assert survivor.data == "base64-encoded-pixels"
    assert survivor.packet_id is None
    assert survivor.aro_id is None
