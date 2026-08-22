import asyncio
import sys
from collections.abc import Awaitable, Callable

from app.data.database.engine import get_db_session
from references.utils import add_callsigns, add_main_commands, add_telemetry

"""
To migrate pre-determined datainto your local database,
you can run `python3 backend/migrate.py` from the top
level directory.

Alternatively, you can include `callsigns`, `commands`, or 'telemetries'
as command arguments to migrate those respective datasets
individually.
"""

# Import type only for annotating the seeding callables below.
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402


async def _run(seeder: Callable[[AsyncSession], Awaitable[None]]) -> None:
    """
    Run a single seeding function inside a fresh async session.

    :param seeder: async function that populates the database using the given session.
    """
    async with get_db_session() as session:
        await seeder(session)


async def main() -> None:
    """
    Parse command-line arguments and run the requested seeding function(s).

    :raises ValueError: if too many arguments are passed or an unknown dataset is requested.
    """
    if len(sys.argv) > 2:
        raise ValueError(f"Invalid input. Expected at most 1 argument, received {len(sys.argv)}")
    elif len(sys.argv[1:]) == 0:
        print("Migrating callsign data...")
        await _run(add_callsigns)
        print("Migrating main command data...")
        await _run(add_main_commands)
        print("Migrating telemetry data...")
        await _run(add_telemetry)
    else:
        match sys.argv[1]:
            case "callsigns":
                print("Migrating callsign data...")
                await _run(add_callsigns)
            case "commands":
                print("Migrating main command data...")
                await _run(add_main_commands)
            case "telemetries":
                print("Migrating telemetry data...")
                await _run(add_telemetry)
            case _:
                raise ValueError("Invalid input. Optional arguments include 'callsigns', 'commands', or 'telemetries'.")


if __name__ == "__main__":
    asyncio.run(main())
