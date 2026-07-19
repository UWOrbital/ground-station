from datetime import UTC, datetime, timedelta
from uuid import UUID

from config.data_config import SESSION_LOCKOUT_SECONDS
from pydantic import EmailStr
from sqlmodel import col, select

from data.data_wrappers.abstract_wrapper import AbstractWrapper  # SEE abstract_wrapper.py FOR LOGIC
from data.database.engine import get_db_session
from data.tables.aro_user_tables import AROUserAuthToken, AROUserCallsigns, AROUserLogin, AROUsers
from data.tables.main_tables import MainCommand, MainTelemetry
from data.tables.mcc_user_tables import MCCUsers
from data.tables.transactional_tables import (
    ARORequest,
    Command,
    CommsSession,
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

    def get_user_by_email(self, email: EmailStr) -> AROUsers | None:
        """
        Find and return a user by their email address.

        :email pydantic.EmailStr
        :returns AROUsers | None
        """
        with get_db_session() as session:
            found_user = session.exec(select(AROUsers).where(AROUsers.email == email)).first()
        return found_user

    def get_user_by_google_id(self, google_id: str) -> AROUsers | None:
        """
        Find and return a user by their Google ID.

        :google_id str
        :returns AROUsers | None
        """
        # Find a user from their Google ID.
        with get_db_session() as session:
            found_user = session.exec(select(AROUsers).where(AROUsers.google_id == google_id)).first()
        return found_user


class AROUserAuthTokenWrapper(AbstractWrapper[AROUserAuthToken, UUID]):
    """
    Data wrapper for AROUserAuthToken table.
    """

    model = AROUserAuthToken

    def get_token_by_token(self, token: str | UUID) -> AROUserAuthToken | None:
        """
        :token str | UUID
        returns AROUserAuthToken | None
        """
        try:
            token_uuid = token if isinstance(token, UUID) else UUID(str(token))
        except ValueError:
            return None
        with get_db_session() as session:
            return session.exec(select(AROUserAuthToken).where(AROUserAuthToken.token == token_uuid)).first()

    def get_token_by_user_id(self, user_id: UUID) -> AROUserAuthToken | None:
        """
        :user_id UUID
        returns AROUserAuthToken | None
        """
        with get_db_session() as session:
            return session.exec(
                select(AROUserAuthToken)
                .where(AROUserAuthToken.user_id == user_id)
                .where(AROUserAuthToken.expiry > datetime.now(UTC))
            ).first()


class AROUserCallsignWrapper(AbstractWrapper[AROUserCallsigns, UUID]):
    """
    Data wrapper for the AROUserCallsigns table.
    """

    model = AROUserCallsigns

    def get_callsign(self, user_cs: str) -> AROUserCallsigns | None:
        """
        :user_cs str
        return AROUserCallsigns | None
        """
        with get_db_session() as session:
            return session.exec(select(AROUserCallsigns).where(AROUserCallsigns.call_sign == user_cs)).first()


class AROUserLoginWrapper(AbstractWrapper[AROUserLogin, UUID]):
    """
    Data wrapper for AROUserLogin table.
    """

    model = AROUserLogin

    def get_login_by_email(self, email: EmailStr) -> AROUserLogin | None:
        """
        Find and return a user by their email address.

        :email pydantic.EmailStr
        :returns AROUserLogin | None
        """
        with get_db_session() as session:
            found_login = session.exec(select(AROUserLogin).where(AROUserLogin.email == email)).first()
        return found_login


class ARORequestWrapper(AbstractWrapper[ARORequest, UUID]):
    """
    Data wrapper for ARORequest table.
    """

    model = ARORequest


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

    def get_most_recent_session(self) -> CommsSession | None:
        """

        Retrieves the Comms session if there is one with the most recent start_time

        :return: CommsSession | None
        """
        with get_db_session() as session:
            return session.exec(select(CommsSession).order_by(col(CommsSession.start_time).desc())).first()

    def get_in_range(
        self, start_after: datetime | None, start_before: datetime | None, limit: int = 100
    ) -> list[CommsSession]:
        """
        Retrieves sessions whose start_time falls within the given range

        :param start_after: only return sessions starting at or after this time
        :param start_before: only return sessions starting before this time
        :param limit: maximum number of rows to return
        :return: matching session entries, ordered by start_time ascending
        """
        with get_db_session() as session:
            query = select(CommsSession)
            if start_after:
                query = query.where(CommsSession.start_time >= start_after)
            if start_before:
                query = query.where(CommsSession.start_time < start_before)
            return list(session.exec(query.order_by(col(CommsSession.start_time).asc()).limit(limit)).all())

    def is_locked_out(self, session_id: UUID) -> bool:
        """
        Checks whether the given session is within its lockout window.

        :param session_id: UUID of the target session.
        :return: True if the session is locked out, False otherwise.
        :raises ValueError: if no session with the given ID exists."""
        session = self.get_by_id(session_id)
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

    def get_by_session(self, session_id: UUID) -> list[Command]:
        """
        Retrieves all commands for a given session.

        :param session_id: UUID of the target session.
        :return: list of Command entries tied to that session.
        """
        with get_db_session() as session:
            return list(session.exec(select(Command).where(Command.session_id == session_id)).all())

    def retrieve_floating_commands(self) -> list[Command]:
        """
        Retrieves all commands which have not yet been assigned to a packet.
        A floating command is any command whose `packet_id` is still null.
        """
        commands = self.get_all()
        floating_commands = [command for command in commands if command.packet_id is None]

        return floating_commands


class TelemetryWrapper(AbstractWrapper[Telemetry, UUID]):
    """
    Data wrapper for Telemetry table.
    """

    model = Telemetry

    def get_most_recent_by_type(self, telemetry_id: int) -> Telemetry | None:
        """

        Get the most recent telemetry filtered by the type id

        :param telemetry_id: The MainTelemetryID to filter by.
            Note: fragile, may break if spreadsheet IDs change.
        :return: Telemetry | None
        """

        with get_db_session() as session:
            return session.exec(select(Telemetry).where(Telemetry.type_ == telemetry_id)).first()

    def get_all_by_type(self, telemetry_id: int) -> list[Telemetry]:
        """
        Retrieves all telemetry filtered by the type id.

        :param telemetry_id: The MainTelemetryID to filter by.
            Note: fragile, may break if spreadsheet IDs change.
        :return: list[Telemetry]
        """
        with get_db_session() as session:
            return list(session.exec(select(Telemetry).where(Telemetry.type_ == telemetry_id)).all())

    def get_all(self) -> list[Telemetry]:
        """
        Retrieves all telemetry.
        :return: list[Telemetry]
        """
        with get_db_session() as session:
            return list(session.exec(select(Telemetry)).all())
