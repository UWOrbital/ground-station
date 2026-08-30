import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.config.db_log_sink import start_db_log_sink, stop_db_log_sink
from app.config.env_settings.backend_config import settings
from app.data.database.engine import get_db_session, setup_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle event for the FastAPI app."""
    # Initialize FastAPI Cache (in memory cache)
    FastAPICache.init(InMemoryBackend())

    # Create the schemas on startup using a fresh async session.
    async with get_db_session() as session:
        await setup_database(session)

    # Start persisting logs to the database (logs.api). Done after the schemas
    # exist so the very first write has somewhere to land.
    start_db_log_sink(asyncio.get_running_loop(), settings.logger)
    try:
        yield
    finally:
        # Flush any buffered log rows before the event loop goes away.
        await stop_db_log_sink()
