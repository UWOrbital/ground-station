from datetime import datetime
from uuid import UUID

from pydantic import EmailStr
from sqlmodel import col, select

from data.data_wrappers.abstract_wrapper import AbstractWrapper  # SEE abstract_wrapper.py FOR LOGIC
from data.database.engine import get_db_session
from data.tables.aro_user_tables import AROUserAuthToken, AROUserCallsigns, AROUserLogin, AROUsers
from data.tables.main_tables import MainCommand, MainTelemetry
from data.tables.mcc_user_tables import MCCUsers
from data.tables.transactional_tables import (
    ARORequest,
    Commands,
    CommsSession,
    Packet,
    PacketCommands,
    PacketTelemetry,
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

    def get_token_by_token(self, token: str) -> AROUserAuthToken | None:
        """
        :token str
        returns AROUserAuthToken | None
        """
        with get_db_session() as session:
            return session.exec(select(AROUserAuthToken).where(AROUserAuthToken.token == token)).first()

    def get_token_by_user_id(self, user_id: UUID) -> AROUserAuthToken | None:
        """
        :user_id UUID
        returns AROUserAuthToken | None
        """
        with get_db_session() as session:
            return session.exec(
                select(AROUserAuthToken)
                .where(AROUserAuthToken.user_data_id == user_id)
                .where(AROUserAuthToken.expiry > datetime.now())
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


class PacketWrapper(AbstractWrapper[Packet, UUID]):
    """
    Data wrapper for Packet table.
    """

    model = Packet


class PacketCommandsWrapper(AbstractWrapper[PacketCommands, UUID]):
    """
    Data wrapper for PacketCommands table.
    """

    model = PacketCommands


class PacketTelemetryWrapper(AbstractWrapper[PacketTelemetry, UUID]):
    """
    Data wrapper for PacketTelemetry table.
    """

    model = PacketTelemetry


class CommandsWrapper(AbstractWrapper[Commands, UUID]):
    """
    Data wrapper for Commands table.
    """

    model = Commands

    def retrieve_floating_commands(self) -> list[Commands]:
        """
        Retrieves all commands which do not have a valid entry in
        the packet_commands table.
        A command which is not valid is considered as any command whose ID
        does not match with any command_id in the packet_commands table
        """
        packet_commands = PacketCommandsWrapper().get_all()
        packet_ids = {packet_command.command_id for packet_command in packet_commands}

        commands = self.get_all()
        floating_commands = [fc for fc in commands if fc.id not in packet_ids]

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
