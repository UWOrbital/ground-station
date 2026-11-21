"""
CLI for the pass predictor.

Run from the backend directory:

cd backend && python -m app.pass_prediction fetch
cd backend && python -m app.pass_prediction add-omm path/to/omm.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from loguru import logger

from app.config.env_settings.pass_prediction_config import PassPredictionConfig
from app.data.database.engine import get_db_engine
from app.pass_prediction.orbit_source import (
    OrbitSourceError,
    add_manual_omm,
    celestrak_client,
    refresh_orbit_elements,
)


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command line parser.

    :return: the parser.
    """
    parser = argparse.ArgumentParser(prog="python -m app.pass_prediction", description="UW Orbital pass predictor")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch", help="download orbit data from CelesTrak if a refresh is needed")
    add_omm = commands.add_parser("add-omm", help="store an OMM record entered by hand")
    add_omm.add_argument("path", type=Path, help="JSON file with one OMM record as an object or in a one-item array")
    return parser


async def run_command(args: argparse.Namespace) -> int:
    """
    Run a parsed command.

    :param args: parsed command line arguments.
    :return: process exit code (0 on success, 1 on failure)
    """
    try:
        if args.command == "fetch":
            config = PassPredictionConfig()
            async with celestrak_client(config) as client:
                await refresh_orbit_elements(config, client)
        elif args.command == "add-omm":
            stored = await add_manual_omm(_load_record(args.path))
            logger.info("Stored orbit elements" if stored else "Orbit elements with that epoch were already stored")
    except (OrbitSourceError, ValueError, OSError) as e:
        logger.error(str(e))
        return 1
    return 0


def _load_record(path: Path) -> object:
    """
    Read one OMM record from a JSON file.

    Accepts a single object or a one-item array.

    :param path: the JSON file.
    :return: the record (not validated yet)
    :raises ValueError: if the file isn't JSON or holds more than one record.
    :raises OSError: if the file can't be read.
    """
    data = json.loads(path.read_text())
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError(f"{path} must contain exactly one OMM record, found {len(data)}")
        return data[0]
    return data


def main(argv: list[str] | None = None) -> int:
    """
    Parse arguments and run the command.

    :param argv: arguments to parse, defaults to command line arguments.
    :return: process exit code.
    """
    args = build_parser().parse_args(argv)

    async def run_and_close() -> int:
        try:
            return await run_command(args)
        finally:
            await get_db_engine().dispose()

    return asyncio.run(run_and_close())


if __name__ == "__main__":
    sys.exit(main())
