import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from data.database.engine import get_db_session, setup_database
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from obc_utils.aro_key_sync_scheduler import run_key_sync_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle event for the FastAPI app."""
    # Initialize FastAPI Cache (in memory cache)
    FastAPICache.init(InMemoryBackend())

    # Must all the get_db_session each time when pass it into a separate function.
    # Otherwise, will get transaction is inactive error
    setup_database(get_db_session())

    # Start the ARO key sync scheduler as a background task
    scheduler_task = asyncio.create_task(run_key_sync_scheduler())

    yield

    # Cancel the scheduler on shutdown
    scheduler_task.cancel()
    with suppress(asyncio.CancelledError):
        await scheduler_task
