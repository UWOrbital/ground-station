from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import delete, update
from sqlmodel import col, select

from app.api.v1.mcc.schemas.responses import TelemetryEntry, TelemetrySubrow
from app.config.data_values import SESSION_LOCKOUT_SECONDS
from app.data.data_wrappers.abstract_wrapper import AbstractWrapper  # SEE abstract_wrapper.py FOR LOGIC
from app.data.database.engine import get_db_session
from app.data.models.aro_user_models import AROUserAuthToken, AROUserCallsigns, AROUserLogin, AROUsers
from app.data.models.main_models import MainCommand, MainTelemetry
from app.data.models.mcc_user_models import MCCUsers
from app.data.models.transactional_models import (
    ARORequest,
    Command,
    CommsSession,
    Image,
    Packet,
    Telemetry,
)


class MCCUsersWrapper(AbstractWrapper[MCCUsers, UUID]):
    """
    Data wrapper for MCCUsers table.
    """

    model = MCCUsers


class AROUsersWrapper(AbstractWrapper[AROUsers, UUID]):
    """
    Data wrapper for AROUsers table.
    """

    model = AROUsers

    async def get_user_by_email(self, email: EmailStr) -> AROUsers | None:
        """
        Find and return a user by their email address.

        :email pydantic.EmailStr
        :returns AROUsers | None
        """
        async with get_db_session() as session:
            found_user = (await session.exec(select(AROUsers).where(AROUsers.email == email))).first()
        return found_user


class AROUserAuthTokenWrapper(AbstractWrapper[AROUserAuthToken, UUID]):
    """
    Data wrapper for AROUserAuthToken table.
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

        async with get_db_session() as session:
            r = await session.exec(
                update(AROUserAuthToken)
                .where(col(token_table.id) == pk)
                .where(col(token_table.rotated_at).is_(None))
                .values(rotated_at=now)
            )
            await session.commit()
            return r.rowcount == 1

    async def revoke_by_family_id(self, family_id: UUID) -> int:
        """
        Atomically revoke every refresh-token row in a family, in one statement.

        :param family_id: the family to revoke.
        :return: number of rows revoked.
        """
        now = datetime.now(UTC)
        token_table = AROUserAuthToken

        async with get_db_session() as session:
            r = await session.exec(
                update(AROUserAuthToken).where(col(token_table.family_id) == family_id).values(revoked_at=now)
            )
            await session.commit()
            return r.rowcount

    async def get_row_by_user_id(self, user_id: UUID) -> AROUserAuthToken | None:
        """
        Retrives the latest (active) refresh token.

        :param user_id: UUID
        :returns: AROUserAuthToken | None
        """
        async with get_db_session() as session:
            return (
                await session.exec(
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
        async with get_db_session() as session:
            r = await session.exec(delete(AROUserAuthToken).where(col(AROUserAuthToken.user_id) == user_id))
            await session.commit()
            return r.rowcount


class AROUserCallsignWrapper(AbstractWrapper[AROUserCallsigns, UUID]):
    """
    Data wrapper for the AROUserCallsigns table.
    """

    model = AROUserCallsigns

    async def get_row_by_callsign(self, user_cs: str) -> AROUserCallsigns | None:
        """
        :user_cs str
        return AROUserCallsigns | None
        """
        async with get_db_session() as session:
            return (await session.exec(select(AROUserCallsigns).where(AROUserCallsigns.call_sign == user_cs))).first()


class AROUserLoginWrapper(AbstractWrapper[AROUserLogin, UUID]):
    """
    Data wrapper for AROUserLogin table.
    """

    model = AROUserLogin

    async def delete_all_by_user_id(self, user_id: UUID) -> int:
        """
        **Deletes** every AROUserLogin row for a user.

        :param user_id: UUID
        :returns: int: number of rows deleted
        """
        async with get_db_session() as session:
            r = await session.exec(delete(AROUserLogin).where(col(AROUserLogin.user_id) == user_id))
            await session.commit()
            return r.rowcount


class ARORequestWrapper(AbstractWrapper[ARORequest, UUID]):
    """
    Data wrapper for ARORequest table.
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
        async with get_db_session() as session:
            return list(
                (
                    await session.exec(
                        select(ARORequest)
                        .where(ARORequest.aro_id == aro_id)
                        .order_by(col(ARORequest.created_on).desc())
                        .limit(count)
                        .offset(offset)
                    )
                ).all()
            )


class MainCommandWrapper(AbstractWrapper[MainCommand, int]):
    """
    Data wrapper for MainCommand table.
    """

    model = MainCommand


class MainTelemetryWrapper(AbstractWrapper[MainTelemetry, int]):
    """
    Data wrapper for MainTelemetry table.
    """

    model = MainTelemetry


class CommsSessionWrapper(AbstractWrapper[CommsSession, UUID]):
    """
    Data wrapper for CommsSession table.
    """

    model = CommsSession

    async def get_most_recent_session(self) -> CommsSession | None:
        """

        Retrieves the Comms session if there is one with the most recent start_time

        :return: CommsSession | None
        """
        async with get_db_session() as session:
            return (await session.exec(select(CommsSession).order_by(col(CommsSession.start_time).desc()))).first()

    async def get_in_range(
        self, start_after: datetime | None, start_before: datetime | None, limit: int = 100
    ) -> list[CommsSession]:
        """
        Retrieves sessions whose start_time falls within the given range

        :param start_after: only return sessions starting at or after this time
        :param start_before: only return sessions starting before this time
        :param limit: maximum number of rows to return
        :return: matching session entries, ordered by start_time ascending
        """
        async with get_db_session() as session:
            query = select(CommsSession)
            if start_after:
                query = query.where(CommsSession.start_time >= start_after)
            if start_before:
                query = query.where(CommsSession.start_time < start_before)
            return list((await session.exec(query.order_by(col(CommsSession.start_time).asc()).limit(limit))).all())

    def is_locked_out(self, session: CommsSession) -> bool:
        """
        Checks whether the given session is within its lockout window.

        :param session: Target session.
        :return: True if the session is locked out, False otherwise.
        :raises ValueError: if no session with the given ID exists."""
        lockout_start = session.start_time - timedelta(seconds=SESSION_LOCKOUT_SECONDS)
        return datetime.now(UTC) >= lockout_start


class PacketWrapper(AbstractWrapper[Packet, UUID]):
    """
    Data wrapper for Packet table.
    """

    model = Packet


class CommandsWrapper(AbstractWrapper[Command, UUID]):
    """
    Data wrapper for Command table.
    """

    model = Command

    async def get_by_session(self, session_id: UUID) -> list[Command]:
        """
        Retrieves all commands for a given session.

        :param session_id: UUID of the target session.
        :return: list of Command entries tied to that session.
        """
        async with get_db_session() as session:
            return list((await session.exec(select(Command).where(Command.session_id == session_id))).all())

    async def retrieve_floating_commands(self) -> list[Command]:
        """
        Retrieves all commands which have not yet been assigned to a packet.
        A floating command is any command whose `packet_id` is still null.
        """
        commands = await self.get_all()
        floating_commands = [command for command in commands if command.packet_id is None]

        return floating_commands


class TelemetryWrapper(AbstractWrapper[Telemetry, UUID]):
    """
    Data wrapper for Telemetry table.
    """

    model = Telemetry

    async def get_most_recent_by_type(self, telemetry_id: int) -> Telemetry | None:
        """

        Get the most recent telemetry filtered by the type id

        :param telemetry_id: The MainTelemetryID to filter by.
            Note: fragile, may break if spreadsheet IDs change.
        :return: Telemetry | None
        """

        async with get_db_session() as session:
            return (await session.exec(select(Telemetry).where(Telemetry.type_ == telemetry_id))).first()

    async def get_all_by_type(self, telemetry_id: int) -> list[Telemetry]:
        """
        Retrieves all telemetry filtered by the type id.

        :param telemetry_id: The MainTelemetryID to filter by.
        :return: list[Telemetry]
        """
        return await self.get_all_by(type_=telemetry_id)

    async def get_all(self) -> list[TelemetryEntry]:  # type: ignore[override]
        """
        Retrieves all telemetry entries, joined with MainTelemetry to expose the type name.

        Uses left outer joins for Packet and CommsSession so that telemetry rows
        without a packet or session assignment are still returned (with subrows
        set to None).

        :return: list[TelemetryEntry]
        """
        async with get_db_session() as session:
            results = (
                await session.execute(
                    select(Telemetry, MainTelemetry.name, Packet.session_id, CommsSession.status)
                    .join(MainTelemetry, Telemetry.type_ == MainTelemetry.id)  # type: ignore[arg-type]
                    .join(Packet, Telemetry.packet_id == Packet.id, isouter=True)  # type: ignore[arg-type]
                    .join(CommsSession, Packet.session_id == CommsSession.id, isouter=True)  # type: ignore[arg-type]
                )
            ).all()
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


class ImageWrapper(AbstractWrapper[Image, UUID]):
    """
    Data wrapper for Image table.
    """

    model = Image

    async def get_latest(self) -> Image | None:
        """
        Return the most recently inserted image, or None if the table is empty.

        :return: the newest Image row, or None.
        """
        async with get_db_session() as session:
            return (await session.exec(select(Image).order_by(col(Image.id).desc()))).first()
