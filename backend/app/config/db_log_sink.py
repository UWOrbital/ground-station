"""
Loguru sink that persists application logs to the ``logs.api`` table.

Loguru sinks are invoked synchronously on the logging thread, but the ground
station's database access is fully async (asyncpg + ``AsyncSession``). To bridge
the two without blocking request handling, the sink only pushes each record onto
an ``asyncio.Queue``; a background consumer task drains that queue and writes
rows in batches.

Two hazards this module is built to avoid:

- **Recursion / log floods.** Writing a row emits ``sqlalchemy.engine`` logs,
  which ``setup_logging`` re-emits through loguru at the custom ``VERBOSE``
  level (15). If those re-entered this sink they would trigger more writes
  forever. The primary guard is the sink's registered level: it is added at
  ``db_sink_min_level`` (default ``INFO`` = 20), so ``VERBOSE`` records are
  dropped by loguru before the filter even runs. ``_db_sink_filter`` then drops
  ``VERBOSE`` again as belt-and-suspenders in case the min level is ever lowered
  below 15.
- **Losing logs or crashing the app.** A DB failure is caught and reported to
  stderr; it never propagates into request handling, and the console sink keeps
  working regardless.
"""

import asyncio
import contextlib
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger

from app.config.env_settings.logger_config import LoggerConfig
from app.data.database.engine import get_db_session
from app.data.models.logs_models import APILog

if TYPE_CHECKING:
    # Message/Record live only in loguru's type stubs, not the runtime package.
    from loguru import Message, Record

# Sentinel pushed onto the queue to tell the consumer to flush and stop.
_SENTINEL: object = object()

# Module-level handles for the running sink. Kept private; managed via
# start_db_log_sink / stop_db_log_sink.
_queue: asyncio.Queue[Any] | None = None
_consumer_task: asyncio.Task[None] | None = None
_loop: asyncio.AbstractEventLoop | None = None
_sink_id: int | None = None


def _db_sink_filter(record: "Record") -> bool:
    """
    Decide whether a loguru record should be persisted to the database.

    Recursion prevention: writing a log row emits SQLAlchemy engine logs, which
    ``setup_logging`` re-emits at the custom ``VERBOSE`` level (15). Those are
    already excluded by the sink's registered level (``db_sink_min_level``,
    default INFO=20); the ``VERBOSE`` check here is a redundant safety net should
    that minimum ever drop below 15.

    :param record: the loguru record dict for the message being logged.
    :return: True if the record should be written to the database, False otherwise.
    """
    return record["level"].name != "VERBOSE"


def _record_to_row(record: "Record") -> dict[str, Any]:
    """
    Map a loguru record onto the ``APILog`` column keyword arguments.

    :param record: the loguru record dict for the message being logged.
    :return: a dict of keyword arguments suitable for ``APILog(**row)``.
    """
    extra = dict(record["extra"]) if record["extra"] else None
    return {
        "time": record["time"],  # timezone-aware datetime supplied by loguru
        "priority": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "extra": _json_safe(extra),
    }


def _json_safe(extra: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Coerce an ``extra`` mapping into JSON-serializable values.

    Values that aren't natively JSON-serializable are stringified so a single odd
    value can never make an entire batch fail to insert.

    :param extra: the loguru ``extra`` mapping, or None.
    :return: a JSON-safe copy of the mapping, or None if there was nothing to store.
    """
    if not extra:
        return None
    safe: dict[str, Any] = {}
    for key, value in extra.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe


async def _write_batch(rows: list[dict[str, Any]]) -> None:
    """
    Insert a batch of log rows, swallowing (and reporting) any DB failure.

    :param rows: ``APILog`` keyword-argument dicts to persist.
    """
    if not rows:
        return
    try:
        async with get_db_session() as session:
            session.add_all([APILog(**row) for row in rows])
            await session.commit()
    except Exception as exc:  # noqa: BLE001 - logging must never crash the app
        print(f"[db_log_sink] failed to write {len(rows)} log row(s): {exc!r}", file=sys.stderr)


async def _consumer(queue: asyncio.Queue[Any], batch_size: int) -> None:
    """
    Drain the queue and persist log rows in batches until told to stop.

    Blocks for the first item, then opportunistically pulls everything currently
    queued (up to ``batch_size``) so bursts collapse into a single INSERT while
    low traffic still writes promptly.

    :param queue: the queue receiving row dicts (and the stop sentinel).
    :param batch_size: maximum number of rows to write per batch.
    """
    while True:
        first = await queue.get()
        if first is _SENTINEL:
            queue.task_done()
            return

        batch: list[dict[str, Any]] = [first]
        queue.task_done()

        stopping = False
        while len(batch) < batch_size:
            try:
                item = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if item is _SENTINEL:
                queue.task_done()
                stopping = True
                break
            batch.append(item)
            queue.task_done()

        await _write_batch(batch)
        if stopping:
            return


def _enqueue(row: dict[str, Any]) -> None:
    """
    Put a row on the queue, dropping it if the buffer is full.

    Runs inside the event loop thread (scheduled via ``call_soon_threadsafe``).

    :param row: the ``APILog`` keyword-argument dict to enqueue.
    """
    if _queue is None:
        return
    try:
        _queue.put_nowait(row)
    except asyncio.QueueFull:
        print("[db_log_sink] log queue full; dropping a log row", file=sys.stderr)


def _sink(message: "Message") -> None:
    """
    Loguru sink callback: hand the record off to the async consumer.

    Kept trivial and non-blocking so it adds no latency to request handling.

    :param message: the loguru ``Message`` whose ``.record`` describes the log.
    """
    if _loop is None or _queue is None:
        return
    row = _record_to_row(message.record)
    # Event loop already closed (e.g. during shutdown); nothing we can do.
    with contextlib.suppress(RuntimeError):
        _loop.call_soon_threadsafe(_enqueue, row)


def start_db_log_sink(loop: asyncio.AbstractEventLoop, config: LoggerConfig) -> None:
    """
    Register the database sink with loguru and start the background writer.

    No-op when ``db_sink_enabled`` is False. Safe to call once per app lifespan.

    :param loop: the running event loop the consumer and enqueues are bound to.
    :param config: the logger configuration controlling the sink.
    """
    global _queue, _consumer_task, _loop, _sink_id

    if not config.db_sink_enabled:
        return
    if _sink_id is not None:
        return  # already started

    _loop = loop
    _queue = asyncio.Queue(maxsize=config.db_sink_queue_maxsize)
    _consumer_task = loop.create_task(_consumer(_queue, config.db_sink_batch_size))
    _sink_id = logger.add(
        _sink,
        level=config.db_sink_min_level,
        filter=_db_sink_filter,
        enqueue=False,  # we do our own async hand-off
    )


async def stop_db_log_sink() -> None:
    """
    Detach the sink and flush any buffered rows before shutdown.

    Removes the loguru handler first so no new records arrive, then signals the
    consumer to drain what remains and awaits it.

    Best-effort: a record whose ``_enqueue`` was already scheduled via
    ``call_soon_threadsafe`` but has not run yet can land behind the sentinel and
    be dropped. That only affects the final handful of rows at shutdown, which is
    an acceptable trade for a bounded, non-blocking flush.
    """
    global _queue, _consumer_task, _loop, _sink_id

    if _sink_id is not None:
        logger.remove(_sink_id)
        _sink_id = None

    if _queue is not None and _consumer_task is not None:
        await _queue.put(_SENTINEL)
        await _consumer_task

    _queue = None
    _consumer_task = None
    _loop = None
