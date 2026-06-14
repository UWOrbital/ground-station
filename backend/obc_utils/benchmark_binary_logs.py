#!/usr/bin/env python3
"""
Benchmark binary log encode/decode throughput at scale.

Compression ratio is fixed per record type (file path → 2-byte ID, etc.) and does
not change with volume — this script measures encode/decode time and verifies
lossless round-trip instead.

Usage (from ground-station repo root):
  PYTHONPATH=backend uv run python backend/obc_utils/benchmark_binary_logs.py
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from obc_utils.log_codec import (
    LEVEL_NAMES,
    decode_log_stream,
    encode_log_entry,
    entry_to_text,
    load_file_id_mapping,
    parse_text_log_line,
)

MESSAGE_TEMPLATES = [
    "Executing log downlink command",
    "Executing OBC reset command",
    "Sending telemetry file",
    "Reached end of telemetry file",
    "Process started to execute safety-critical command",
    "Starting RTC Demo",
    "CC1120 SPI read test passed.",
]

ERROR_CODES = [2, 3, 5, 8, 15, 100, 301, 801, 1001, 1500]
FILE_PATHS = load_file_id_mapping()


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    record_count: int
    text_bytes: int
    binary_bytes: int
    round_trip_ok: bool
    encode_seconds: float
    decode_seconds: float
    mismatches: int

    @property
    def encode_records_per_sec(self) -> float:
        return self.record_count / self.encode_seconds if self.encode_seconds else 0.0

    @property
    def decode_records_per_sec(self) -> float:
        return self.record_count / self.decode_seconds if self.decode_seconds else 0.0


def _make_text_line(index: int, rng: random.Random) -> str:
    path = FILE_PATHS[rng.randrange(len(FILE_PATHS))]
    line_no = rng.randrange(1, 500)
    level = rng.choice(LEVEL_NAMES[:6])
    ts = 1749483000 + index
    dt = datetime.fromtimestamp(ts, tz=UTC)
    prefix = f"{dt.year % 100:02d}-{dt.month:02d}-{dt.day:02d}_{dt.hour:02d}-{dt.minute:02d}-{dt.second:02d} "

    if rng.random() < 0.30:
        payload = str(rng.choice(ERROR_CODES))
    else:
        payload = rng.choice(MESSAGE_TEMPLATES)
        if rng.random() < 0.10:
            payload = payload + f" (seq={index})"

    return f"{prefix}{level:<5} -> {path}:{line_no} - {payload}"


def run_benchmark(record_count: int, seed: int = 42) -> BenchmarkResult:
    rng = random.Random(seed)
    text_lines = [_make_text_line(i, rng) for i in range(record_count)]
    text_blob = ("\n".join(text_lines) + "\n").encode()

    encode_start = time.perf_counter()
    binary = bytearray()
    for line in text_lines:
        binary.extend(encode_log_entry(parse_text_log_line(line)))
    encode_seconds = time.perf_counter() - encode_start

    decode_start = time.perf_counter()
    decoded_entries = decode_log_stream(bytes(binary))
    decode_seconds = time.perf_counter() - decode_start

    if record_count <= 100_000:
        decoded_lines = [entry_to_text(entry) for entry in decoded_entries]
        mismatches = sum(1 for original, decoded in zip(text_lines, decoded_lines, strict=True) if original != decoded)
        round_trip_ok = mismatches == 0 and len(decoded_lines) == record_count
    else:
        check_indices = {0, record_count - 1, record_count // 2}
        check_indices.update(range(0, record_count, max(1, record_count // 1000)))
        mismatches = 0
        if len(decoded_entries) != record_count:
            mismatches = abs(len(decoded_entries) - record_count)
            round_trip_ok = False
        else:
            mismatches = sum(1 for i in check_indices if entry_to_text(decoded_entries[i]) != text_lines[i])
            round_trip_ok = mismatches == 0

    return BenchmarkResult(
        record_count=record_count,
        text_bytes=len(text_blob),
        binary_bytes=len(binary),
        round_trip_ok=round_trip_ok,
        encode_seconds=encode_seconds,
        decode_seconds=decode_seconds,
        mismatches=mismatches,
    )


def _format_row(result: BenchmarkResult) -> str:
    round_trip = "YES" if result.round_trip_ok else f"NO ({result.mismatches})"
    if result.record_count > 100_000 and result.round_trip_ok:
        round_trip += " (spot-checked)"
    return (
        f"| {result.record_count:,} | {result.text_bytes / 1_048_576:.1f} | "
        f"{result.binary_bytes / 1_048_576:.1f} | "
        f"{result.encode_records_per_sec:,.0f} | {result.decode_records_per_sec:,.0f} | "
        f"{result.encode_seconds:.2f}s | {result.decode_seconds:.2f}s | {round_trip} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--records",
        type=int,
        nargs="+",
        default=[10_000, 100_000, 1_000_000],
        help="Record counts to benchmark",
    )
    args = parser.parse_args()

    results = [run_benchmark(count) for count in args.records]

    print("Binary log encode/decode benchmark")
    print("Mix: ~70% messages, ~30% error codes. Ratio is per-record-type, not volume-dependent.")
    print()
    print("| Records | Text (MB) | Binary (MB) | Encode (rec/s) | Decode (rec/s) | Encode | Decode | Round-trip |")
    print("|---------|-----------|-------------|----------------|----------------|--------|--------|------------|")
    for result in results:
        print(_format_row(result))

    if not all(r.round_trip_ok for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
