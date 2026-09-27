import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.config.db_log_sink import start_db_log_sink, stop_db_log_sink
from app.config.env_settings.backend_config import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle event for the FastAPI app."""
    # Initialize FastAPI Cache (in memory cache)
    FastAPICache.init(InMemoryBackend())

    # Start persisting logs to the database (logs.api). Migrations must already
    # have created the schema before the application starts.
    start_db_log_sink(asyncio.get_running_loop(), settings.logger)
    try:
        yield
    finally:
        # Flush any buffered log rows before the event loop goes away.
        await stop_db_log_sink()
