from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col, select

from app.api.mcc.schemas.responses import TelemetryEntry, TelemetrySubrow
from app.config.data_values import SESSION_LOCKOUT_SECONDS
from app.data.database.engine import get_db_session
from app.data.enums.transactional import OrbitElementSource, SessionSource, SessionStatus
from app.data.models.aro_user_models import AROUserAuthToken, AROUserCallsigns, AROUserLogin, AROUsers
from app.data.models.logs_models import APILog
from app.data.models.main_models import MainCommand, MainTelemetry
from app.data.models.mcc_user_models import MCCUsers
from app.data.models.transactional_models import (
    ARORequest,
    Command,
    Image,
    OrbitElement,
    OrbitFetchAttempt,
    Packet,
    Session,
    Telemetry,
)
from app.data.repositories.abstract_repository import AbstractRepository  # SEE abstract_repository.py FOR LOGIC


class MCCUsersRepository(AbstractRepository[MCCUsers, UUID]):
    """
    Repository for MCCUsers table.
    """

    model = MCCUsers


class AROUsersRepository(AbstractRepository[AROUsers, UUID]):
    """
    Repository for AROUsers table.
    """

    model = AROUsers

    async def get_user_by_email(self, email: EmailStr) -> AROUsers | None:
        """
        Find and return a user by their email address.

        :email pydantic.EmailStr
        :returns AROUsers | None
        """
        async with get_db_session() as db:
            found_user = (await db.exec(select(AROUsers).where(AROUsers.email == email))).first()
        return found_user


class AROUserAuthTokenRepository(AbstractRepository[AROUserAuthToken, UUID]):
    """
    Repository for AROUserAuthToken table.
    """

    model = AROUserAuthToken

    async def claim_rotation(self, pk: UUID) -> bool:
        """
        Atomically mark a refresh-token row as rotated, iff it hasn't been already.

        Single conditional UPDATE rather than a read-then-write, so two
        concurrent callers can't both believe they won the rotation.

        :param pk: id of the AROUserAuthToken row being rotated.
        :return: True if this call was the one that claimed the rotation,
            False if the row was already rotated (or doesn't exist).
        """
        now = datetime.now(UTC)
        token_table = AROUserAuthToken

        async with get_db_session() as db:
            r = await db.exec(
                update(AROUserAuthToken)
                .where(col(token_table.id) == pk)
                .where(col(token_table.rotated_at).is_(None))
                .values(rotated_at=now)
            )
            await db.commit()
            return r.rowcount == 1

    async def revoke_by_family_id(self, family_id: UUID) -> int:
        """
        Atomically revoke every refresh-token row in a family, in one statement.

        :param family_id: the family to revoke.
        :return: number of rows revoked.
        """
        now = datetime.now(UTC)
        token_table = AROUserAuthToken

        async with get_db_session() as db:
            r = await db.exec(
                update(AROUserAuthToken).where(col(token_table.family_id) == family_id).values(revoked_at=now)
            )
            await db.commit()
            return r.rowcount

    async def get_row_by_user_id(self, user_id: UUID) -> AROUserAuthToken | None:
        """
        Retrives the latest (active) refresh token.

        :param user_id: UUID
        :returns: AROUserAuthToken | None
        """
        async with get_db_session() as db:
            return (
                await db.exec(
                    select(AROUserAuthToken)
                    .where(AROUserAuthToken.user_id == user_id)
                    .where(AROUserAuthToken.expiry > datetime.now(UTC))
                )
            ).first()

    async def delete_all_by_user_id(self, user_id: UUID) -> int:
        """
        **Deletes** every AROUserAuthToken row for a user.

        :param user_id: UUID
        :returns: int: number of rows deleted
        """
        async with get_db_session() as db:
            r = await db.exec(delete(AROUserAuthToken).where(col(AROUserAuthToken.user_id) == user_id))
            await db.commit()
            return r.rowcount


class AROUserCallsignRepository(AbstractRepository[AROUserCallsigns, UUID]):
    """
    Repository for the AROUserCallsigns table.
    """

    model = AROUserCallsigns

    async def get_row_by_callsign(self, user_cs: str) -> AROUserCallsigns | None:
        """
        :user_cs str
        return AROUserCallsigns | None
        """
        async with get_db_session() as db:
            return (await db.exec(select(AROUserCallsigns).where(AROUserCallsigns.call_sign == user_cs))).first()


class AROUserLoginRepository(AbstractRepository[AROUserLogin, UUID]):
    """
    Repository for AROUserLogin table.
    """

    model = AROUserLogin

    async def delete_all_by_user_id(self, user_id: UUID) -> int:
        """
        **Deletes** every AROUserLogin row for a user.

        :param user_id: UUID
        :returns: int: number of rows deleted
        """
        async with get_db_session() as db:
            r = await db.exec(delete(AROUserLogin).where(col(AROUserLogin.user_id) == user_id))
            await db.commit()
            return r.rowcount


class ARORequestRepository(AbstractRepository[ARORequest, UUID]):
    """
    Repository for ARORequest table.
    """

    model = ARORequest

    async def get_recent_by_aro(self, aro_id: UUID, count: int, offset: int) -> list[ARORequest]:
        """
        Retrieves a most-recent-first page of a single ARO's picture requests.

        :param aro_id: the owning ARO user's id.
        :param count: maximum number of requests to return.
        :param offset: number of most-recent requests to skip (for paging).
        :return: the requested page of ARORequest rows, newest first.
        """
        async with get_db_session() as db:
            return list(
                (
                    await db.exec(
                        select(ARORequest)
                        .where(ARORequest.aro_id == aro_id)
                        .order_by(col(ARORequest.created_on).desc())
                        .limit(count)
                        .offset(offset)
                    )
                ).all()
            )

    async def get_recent(self, count: int, offset: int) -> list[ARORequest]:
        """
        Retrieves a most-recent-first page of every ARO's picture requests.

        :param count: maximum number of requests to return.
        :param offset: number of most-recent requests to skip (for paging).
        :return: the requested page of ARORequest rows, newest first.
        """
        async with get_db_session() as db:
            return list(
                (
                    await db.exec(
                        select(ARORequest).order_by(col(ARORequest.created_on).desc()).limit(count).offset(offset)
                    )
                ).all()
            )


class MainCommandRepository(AbstractRepository[MainCommand, int]):
    """
    Repository for MainCommand table.
    """

    model = MainCommand


class MainTelemetryRepository(AbstractRepository[MainTelemetry, int]):
    """
    Repository for MainTelemetry table.
    """

    model = MainTelemetry


class SessionRepository(AbstractRepository[Session, UUID]):
    """
    Repository for Session table.
    """

    model = Session

    async def get_in_range(
        self,
        start_after: datetime | None,
        start_before: datetime | None,
        limit: int = 100,
        offset: int = 0,
        end_after: datetime | None = None,
        source: SessionSource | None = None,
        status: SessionStatus | None = None,
    ) -> list[Session]:
        """
        Retrieves sessions matching the given time range and filters

        :param start_after: only return sessions starting at or after this time
        :param start_before: only return sessions starting before this time
        :param limit: maximum number of rows to return
        :param offset: number of rows to skip
        :param end_after: only return sessions ending after this time
        :param source: only return sessions with this source
        :param status: only return sessions with this status
        :return: matching session entries, ordered by start_time ascending
        """
        async with get_db_session() as db:
            query = select(Session)
            if start_after:
                query = query.where(Session.start_time >= start_after)
            if start_before:
                query = query.where(Session.start_time < start_before)
            if end_after:
                query = query.where(Session.end_time > end_after)
            if source:
                query = query.where(Session.source == source)
            if status:
                query = query.where(Session.status == status)
            query = query.order_by(col(Session.start_time).asc()).offset(offset).limit(limit)
            return list((await db.exec(query)).all())

    async def get_current_or_next(self, now: datetime | None = None) -> Session | None:
        """
        Retrieves the session in progress, or the next upcoming session

        :param now: reference time (defaults to the current UTC time)
        :return: the current or next session, or None if no session ends after now
        """
        reference = now or datetime.now(UTC)
        async with get_db_session() as db:
            query = select(Session).where(Session.end_time > reference).order_by(col(Session.start_time).asc()).limit(1)
            return (await db.exec(query)).first()

    def is_locked_out(self, session: Session) -> bool:
        """
        Checks whether the given session is within its lockout window.

        :param session: Target session.
        :return: True if the session is locked out, False otherwise.
        :raises ValueError: if no session with the given ID exists."""
        lockout_start = session.start_time - timedelta(seconds=SESSION_LOCKOUT_SECONDS)
        return datetime.now(UTC) >= lockout_start


class OrbitElementRepository(AbstractRepository[OrbitElement, UUID]):
    """
    Repository for OrbitElement table.
    """

    model = OrbitElement

    async def get_latest(self, norad_cat_id: int) -> OrbitElement | None:
        """
        Retrieves the orbit elements with the most recent epoch for a satellite

        :param norad_cat_id: NORAD catalog number of the satellite
        :return: the newest orbit elements, or None if none exist
        """
        async with get_db_session() as db:
            query = (
                select(OrbitElement)
                .where(OrbitElement.norad_cat_id == norad_cat_id)
                .order_by(col(OrbitElement.epoch).desc())
                .limit(1)
            )
            return (await db.exec(query)).first()

    async def insert_if_new(
        self, norad_cat_id: int, epoch: datetime, omm: dict[str, Any], source: OrbitElementSource
    ) -> bool:
        """
        Stores orbit elements unless elements with the same epoch already exist for the satellite

        Since CelesTrak serves the same element set until the next update, re-downloading is normal
        and should not create a duplicate row
        
        :param norad_cat_id: NORAD catalog number of the satellite
        :param epoch: epoch of the elements (with timezone)
        :param omm: the OMM record
        :param source: where the elements came from
        :return: True if a new row was stored, False if these elements were already stored
        """
        statement = (
            pg_insert(OrbitElement)
            .values(
                id=uuid4(),
                norad_cat_id=norad_cat_id,
                epoch=epoch,
                omm=omm,
                source=source,
                created_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(constraint="uq_orbit_elements_norad_cat_id_epoch")
            .returning(col(OrbitElement.id))
        )
        async with get_db_session() as db:
            result = await db.exec(statement)
            inserted = result.first() is not None
            await db.commit()
            return inserted


class OrbitFetchAttemptRepository(AbstractRepository[OrbitFetchAttempt, UUID]):
    """
    Repository for OrbitFetchElement table.
    """

    model = OrbitFetchAttempt

    async def get_latest(self, norad_cat_id: int) -> OrbitFetchAttempt | None:
        """
        Retrieves the most recent fetch attempt for a satellite
        
        :param norad_cat_id: NORAD catalog number of the satellite
        :return: the latest attempt, or None if none exists
        """
        async with get_db_session() as db:
            query = (
                select(OrbitFetchAttempt)
                .where(OrbitFetchAttempt.norad_cat_id == norad_cat_id)
                .order_by(col(OrbitFetchAttempt.attempted_at).desc())
                .limit(1)
            )
            return (await db.exec(query)).first()


class PacketRepository(AbstractRepository[Packet, UUID]):
    """
    Repository for Packet table.
    """

    model = Packet


class CommandsRepository(AbstractRepository[Command, UUID]):
    """
    Repository for Command table.
    """

    model = Command

    async def get_by_session(self, session_id: UUID) -> list[Command]:
        """
        Retrieves all commands for a given session.

        :param session_id: UUID of the target session.
        :return: list of Command entries tied to that session.
        """
        async with get_db_session() as db:
            return list((await db.exec(select(Command).where(Command.session_id == session_id))).all())

    async def retrieve_floating_commands(self) -> list[Command]:
        """
        Retrieves all commands which have not yet been assigned to a packet.
        A floating command is any command whose `packet_id` is still null.
        """
        commands = await self.get_all()
        floating_commands = [command for command in commands if command.packet_id is None]

        return floating_commands


class TelemetryRepository(AbstractRepository[Telemetry, UUID]):
    """
    Repository for Telemetry table.
    """

    model = Telemetry

    async def get_most_recent_by_type(self, telemetry_id: int) -> Telemetry | None:
        """

        Get the most recent telemetry filtered by the type id

        :param telemetry_id: The MainTelemetryID to filter by.
            Note: fragile, may break if spreadsheet IDs change.
        :return: Telemetry | None
        """

        async with get_db_session() as db:
            query = (
                select(Telemetry)
                .where(Telemetry.type_ == telemetry_id)
                .order_by(col(Telemetry.timestamp).desc())
                .limit(1)
            )
            return (await db.exec(query)).first()

    async def get_all_by_type(self, telemetry_id: int) -> list[Telemetry]:
        """
        Retrieves all telemetry filtered by the type id.

        :param telemetry_id: The MainTelemetryID to filter by.
        :return: list[Telemetry]
        """
        return await self.get_all_by(type_=telemetry_id)

    async def get_all(self, limit: int | None = None, offset: int = 0) -> list[TelemetryEntry]:  # type: ignore[override]
        """
        Retrieves all telemetry entries, joined with MainTelemetry to expose the type name.

        Uses left outer joins for Packet and Session so that telemetry rows
        without a packet or session assignment are still returned (with subrows
        set to None).

        :return: list[TelemetryEntry]
        """
        async with get_db_session() as db:
            query = (
                select(Telemetry, MainTelemetry.name, Packet.session_id, Session.status)
                .join(MainTelemetry, Telemetry.type_ == MainTelemetry.id)  # type: ignore[arg-type]
                .join(Packet, Telemetry.packet_id == Packet.id, isouter=True)  # type: ignore[arg-type]
                .join(Session, Packet.session_id == Session.id, isouter=True)  # type: ignore[arg-type]
                .order_by(col(Telemetry.id))
            )
            if offset:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            results = (await db.exec(query)).all()
            return [
                TelemetryEntry(
                    id=t.id,
                    type=name,
                    value=t.value,
                    timestamp=t.timestamp,
                    subrows=[
                        TelemetrySubrow(
                            packet=str(t.packet_id) if t.packet_id else "",
                            session=str(session_id) if session_id else "",
                            obc_state=str(status) if status else "",
                        )
                    ],
                )
                for t, name, session_id, status in results
            ]


class APILogRepository(AbstractRepository[APILog, UUID]):
    """
    Repository for the APILog table (logs.api).
    """

    model = APILog

    async def get_recent(self, limit: int = 100) -> list[APILog]:
        """
        Retrieve the most recent log rows, newest first.

        Intended for a future monitoring surface or ad-hoc inspection; the loguru
        sink writes rows via a batched consumer, not through this repository.

        :param limit: maximum number of rows to return.
        :return: the newest APILog rows, ordered by time descending.
        """
        async with get_db_session() as db:
            return list((await db.exec(select(APILog).order_by(col(APILog.time).desc()).limit(limit))).all())


class ImageRepository(AbstractRepository[Image, UUID]):
    """
    Repository for Image table.
    """

    model = Image

    async def get_latest(self) -> Image | None:
        """
        Return the most recently inserted image, or None if the table is empty.

        :return: the newest Image row, or None.
        """
        async with get_db_session() as db:
            return (await db.exec(select(Image).order_by(col(Image.id).desc()))).first()
