from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.data.models.aro_user_models import AROUserCallsigns
from app.data.models.main_models import MainCommand, MainTelemetry
from references.callsigns import callsigns
from references.main_commands import main_commands
from references.main_telemetry import main_telemetry


async def add_main_commands(session: AsyncSession) -> None:
    """
    Setup the main commands to the database
    """
    query = select(MainCommand).limit(1)  # Check if the db is empty
    result = (await session.exec(query)).first()
    if not result:
        session.add_all(main_commands())
        await session.commit()


async def add_callsigns(session: AsyncSession) -> None:
    """
    Setup the valid callsigns to the database
    """
    query = select(AROUserCallsigns).limit(1)
    result = (await session.exec(query)).first()
    if not result:
        session.add_all(callsigns())
        await session.commit()


async def add_telemetry(session: AsyncSession) -> None:
    """
    Setup the main telemetry to the database
    """
    query = select(MainTelemetry).limit(1)  # Check if the db is empty
    result = (await session.exec(query)).first()
    if not result:
        session.add_all(main_telemetry())
        await session.commit()
