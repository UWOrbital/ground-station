from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from app.data.enums.transactional import OrbitElementSource, SessionSource, SessionStatus
from app.data.models.transactional_models import OrbitElement, Session
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import OrbitElementRepository, SessionRepository
from sqlmodel.ext.asyncio.session import AsyncSession

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def _manual(start: datetime, minutes: int = 10, status: SessionStatus = SessionStatus.PENDING) -> Session:
    """Build an unsaved manual session.

    :param start: session start time
    :param minutes: session length in minutes
    :param status: session status
    :return: an unsaved Session
    """
    return Session(start_time=start, end_time=start + timedelta(minutes=minutes), status=status)


async def _save(db_session: AsyncSession, *sessions: Session) -> None:
    """Save the given sessions.

    :param db_session: test database session
    :param sessions: sessions to insert
    """
    db_session.add_all(sessions)
    await db_session.commit()


def test_dal_registers_session_repositories() -> None:
    assert DAL.sessions is SessionRepository
    assert DAL.orbit_elements is OrbitElementRepository


# ----------------------------------------------SessionRepository.get_in_range---------------------------------------------- #


async def test_get_in_range_no_filters_ordered(db_session: AsyncSession) -> None:
    later = _manual(NOW + timedelta(hours=2))
    earlier = _manual(NOW - timedelta(hours=2))
    middle = _manual(NOW)
    await _save(db_session, later, earlier, middle)

    result = await DAL.sessions().get_in_range(None, None)

    assert [s.id for s in result] == [earlier.id, middle.id, later.id]


async def test_get_in_range_start_bounds(db_session: AsyncSession) -> None:
    """start_after is inclusive and start_before is exclusive."""
    at_after = _manual(NOW)
    inside = _manual(NOW + timedelta(minutes=30))
    at_before = _manual(NOW + timedelta(hours=1))
    before_range = _manual(NOW - timedelta(minutes=30))
    await _save(db_session, at_after, inside, at_before, before_range)

    result = await DAL.sessions().get_in_range(NOW, NOW + timedelta(hours=1))

    assert [s.id for s in result] == [at_after.id, inside.id]


async def test_get_in_range_end_after_includes_running_session(db_session: AsyncSession) -> None:
    running = _manual(NOW - timedelta(minutes=2), minutes=7)
    finished = _manual(NOW - timedelta(minutes=30), minutes=10)
    ends_exactly_now = _manual(NOW - timedelta(minutes=10), minutes=10)
    upcoming = _manual(NOW + timedelta(minutes=30))
    await _save(db_session, running, finished, ends_exactly_now, upcoming)

    by_end = await DAL.sessions().get_in_range(None, None, end_after=NOW)
    by_start = await DAL.sessions().get_in_range(NOW, None)

    assert [s.id for s in by_end] == [running.id, upcoming.id]
    assert [s.id for s in by_start] == [upcoming.id]


async def test_get_in_range_source_filter(
    db_session: AsyncSession, make_predicted_session: Callable[..., Session]
) -> None:
    manual = _manual(NOW)
    predicted = make_predicted_session(NOW + timedelta(hours=1))
    await _save(db_session, manual, predicted)

    manual_only = await DAL.sessions().get_in_range(None, None, source=SessionSource.MANUAL)
    predicted_only = await DAL.sessions().get_in_range(None, None, source=SessionSource.PREDICTED)

    assert [s.id for s in manual_only] == [manual.id]
    assert [s.id for s in predicted_only] == [predicted.id]


async def test_get_in_range_status_filter(db_session: AsyncSession) -> None:
    pending = _manual(NOW, status=SessionStatus.PENDING)
    scheduled = _manual(NOW + timedelta(hours=1), status=SessionStatus.SCHEDULED)
    completed = _manual(NOW - timedelta(hours=1), status=SessionStatus.COMPLETED)
    await _save(db_session, pending, scheduled, completed)

    result = await DAL.sessions().get_in_range(None, None, status=SessionStatus.SCHEDULED)

    assert [s.id for s in result] == [scheduled.id]


async def test_get_in_range_filters_combine(
    db_session: AsyncSession, make_predicted_session: Callable[..., Session]
) -> None:
    match = make_predicted_session(NOW + timedelta(hours=1), status=SessionStatus.SCHEDULED)
    wrong_status = make_predicted_session(NOW + timedelta(hours=2))
    wrong_source = _manual(NOW + timedelta(hours=3), status=SessionStatus.SCHEDULED)
    already_ended = make_predicted_session(NOW - timedelta(hours=1), status=SessionStatus.SCHEDULED)
    await _save(db_session, match, wrong_status, wrong_source, already_ended)

    result = await DAL.sessions().get_in_range(
        None, None, end_after=NOW, source=SessionSource.PREDICTED, status=SessionStatus.SCHEDULED
    )

    assert [s.id for s in result] == [match.id]


async def test_get_in_range_limit_and_offset(db_session: AsyncSession) -> None:
    sessions = [_manual(NOW + timedelta(hours=i)) for i in range(4)]
    await _save(db_session, *sessions)

    page = await DAL.sessions().get_in_range(None, None, limit=2, offset=1)
    past_end = await DAL.sessions().get_in_range(None, None, limit=2, offset=4)

    assert [s.id for s in page] == [sessions[1].id, sessions[2].id]
    assert past_end == []


# -------------------------------------------SessionRepository.get_current_or_next------------------------------------------- #


async def test_current_or_next_prefers_running(db_session: AsyncSession) -> None:
    running = _manual(NOW - timedelta(minutes=2), minutes=7)
    upcoming = _manual(NOW + timedelta(minutes=30))
    past = _manual(NOW - timedelta(hours=1))
    await _save(db_session, upcoming, running, past)

    result = await DAL.sessions().get_current_or_next(NOW)

    assert result is not None
    assert result.id == running.id


async def test_current_or_next_returns_soonest_upcoming(db_session: AsyncSession) -> None:
    """With nothing running, the earliest upcoming session is returned."""
    soon = _manual(NOW + timedelta(minutes=30))
    later = _manual(NOW + timedelta(hours=3))
    past = _manual(NOW - timedelta(hours=1))
    await _save(db_session, later, soon, past)

    result = await DAL.sessions().get_current_or_next(NOW)

    assert result is not None
    assert result.id == soon.id


async def test_current_or_next_session_ending_now_is_over(db_session: AsyncSession) -> None:
    """A session with end_time = reference time doesn't count as current."""
    ending = _manual(NOW - timedelta(minutes=10), minutes=10)
    upcoming = _manual(NOW + timedelta(minutes=5))
    await _save(db_session, ending, upcoming)

    result = await DAL.sessions().get_current_or_next(NOW)

    assert result is not None
    assert result.id == upcoming.id


@pytest.mark.parametrize("with_past_sessions", [False, True])
async def test_current_or_next_none(db_session: AsyncSession, with_past_sessions: bool) -> None:
    """None is returned when no session ends after the reference time.

    :param with_past_sessions: whether finished sessions exist in the table.
    """
    if with_past_sessions:
        await _save(db_session, _manual(NOW - timedelta(hours=2)), _manual(NOW - timedelta(hours=1)))

    assert await DAL.sessions().get_current_or_next(NOW) is None


async def test_current_or_next_defaults_to_current_time(db_session: AsyncSession) -> None:
    """Without an reference time, the current UTC time is used by default."""
    real_now = datetime.now(UTC)
    running = _manual(real_now - timedelta(minutes=1), minutes=10)
    stale = _manual(real_now - timedelta(hours=2))
    await _save(db_session, stale, running)

    result = await DAL.sessions().get_current_or_next()

    assert result is not None
    assert result.id == running.id


# ----------------------------------------------OrbitElementRepository.get_latest---------------------------------------------- #


async def test_get_latest_returns_newest_epoch(db_session: AsyncSession) -> None:
    """The element set with the newest epoch for the requested satellite is returned."""
    older = OrbitElement(norad_cat_id=25544, epoch=datetime(2026, 11, 17, tzinfo=UTC), omm={"v": "older"})
    newer = OrbitElement(norad_cat_id=25544, epoch=datetime(2026, 11, 18, tzinfo=UTC), omm={"v": "newer"})
    # Newest overall, but for a different satellite
    other = OrbitElement(norad_cat_id=99999, epoch=datetime(2026, 11, 19, tzinfo=UTC), omm={"v": "other"})
    # Inserted last so insertion order can't replace epoch order
    db_session.add_all([newer, other, older])
    await db_session.commit()

    result = await DAL.orbit_elements().get_latest(25544)

    assert result is not None
    assert result.id == newer.id
    assert result.omm == {"v": "newer"}


async def test_get_latest_any_source(db_session: AsyncSession) -> None:
    celestrak = OrbitElement(norad_cat_id=25544, epoch=datetime(2026, 11, 17, tzinfo=UTC), omm={})
    manual = OrbitElement(
        norad_cat_id=25544, epoch=datetime(2026, 11, 18, tzinfo=UTC), omm={}, source=OrbitElementSource.MANUAL
    )
    db_session.add_all([celestrak, manual])
    await db_session.commit()

    result = await DAL.orbit_elements().get_latest(25544)

    assert result is not None
    assert result.id == manual.id


async def test_get_latest_unknown_satellite(orbit_element: OrbitElement) -> None:
    """None is returned for a catalog number with no stored elements.

    :param orbit_element: an unrelated stored element set, so the table isn't empty.
    """
    assert await DAL.orbit_elements().get_latest(12345) is None


async def test_get_orbit_element_by_id(orbit_element: OrbitElement) -> None:
    """The tracker's lookup by ID uses get_by_id.

    :param orbit_element: stored element set to look up.
    """
    result = await DAL.orbit_elements().get_by_id(orbit_element.id)
    assert result.norad_cat_id == orbit_element.norad_cat_id
