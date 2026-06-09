"""
Tests for the OBC binary log codec.

The golden vectors in this file are shared with the OBC-firmware GoogleTest
suite (test/unit/test_log_codec.cpp). If the binary format changes, both test
suites must be updated together.
"""

import pytest
from obc_utils.log_codec import (
    FILE_ID_UNKNOWN,
    LEVEL_NAMES,
    LogCodecError,
    LogEntry,
    decode_log_entry,
    decode_log_stream,
    encode_log_entry,
    entry_to_text,
    file_id_from_path,
    file_path_from_id,
    load_file_id_mapping,
    parse_text_log_line,
)

# 2025-01-01 00:00:00 UTC
TS_2025_01_01 = 1735689600

# Must match TestLogCodec.GoldenVectorErrorCode in OBC-firmware
GOLDEN_ERROR_ENTRY = LogEntry(
    level=LEVEL_NAMES.index("ERROR"),
    is_msg=False,
    file_id=7,
    line=123,
    timestamp=TS_2025_01_01,
    err_code=301,
)
GOLDEN_ERROR_BYTES = bytes(
    [0xA8, 0x14, 0x07, 0x00, 0x7B, 0x00, 0x80, 0x85, 0x74, 0x67, 0x2D, 0x01, 0x00, 0x00]
)

# Must match TestLogCodec.GoldenVectorMsg in OBC-firmware
GOLDEN_MSG_ENTRY = LogEntry(
    level=LEVEL_NAMES.index("DEBUG"),
    is_msg=True,
    file_id=2,
    line=10,
    msg="Hi",
)
GOLDEN_MSG_BYTES = bytes([0xA8, 0x09, 0x02, 0x00, 0x0A, 0x00, 0x02, ord("H"), ord("i")])


def test_golden_vector_error_code_encode():
    assert encode_log_entry(GOLDEN_ERROR_ENTRY) == GOLDEN_ERROR_BYTES


def test_golden_vector_error_code_decode():
    entry, consumed = decode_log_entry(GOLDEN_ERROR_BYTES)
    assert consumed == len(GOLDEN_ERROR_BYTES)
    assert entry.level_name == "ERROR"
    assert entry.is_msg is False
    assert entry.file_id == 7
    assert entry.line == 123
    assert entry.timestamp == TS_2025_01_01
    assert entry.err_code == 301


def test_golden_vector_msg_encode():
    assert encode_log_entry(GOLDEN_MSG_ENTRY) == GOLDEN_MSG_BYTES


def test_golden_vector_msg_decode():
    entry, consumed = decode_log_entry(GOLDEN_MSG_BYTES)
    assert consumed == len(GOLDEN_MSG_BYTES)
    assert entry.level_name == "DEBUG"
    assert entry.is_msg is True
    assert entry.timestamp is None
    assert entry.msg == "Hi"


@pytest.mark.parametrize(
    "entry",
    [
        LogEntry(level=0, is_msg=True, file_id=0, line=1, msg="trace msg"),
        LogEntry(level=4, is_msg=False, file_id=44, line=65535, timestamp=TS_2025_01_01, err_code=1001),
        LogEntry(level=5, is_msg=True, file_id=FILE_ID_UNKNOWN, line=0, timestamp=0x12345678, msg=""),
        LogEntry(level=2, is_msg=True, file_id=3, line=42, msg="a" * 128),
    ],
)
def test_encode_decode_round_trip(entry):
    encoded = encode_log_entry(entry)
    decoded, consumed = decode_log_entry(encoded)
    assert consumed == len(encoded)
    assert decoded.level == entry.level
    assert decoded.is_msg == entry.is_msg
    assert decoded.file_id == entry.file_id
    assert decoded.line == entry.line
    assert decoded.timestamp == entry.timestamp
    assert decoded.err_code == entry.err_code
    assert decoded.msg == entry.msg


def test_decode_rejects_bad_sync_byte():
    with pytest.raises(LogCodecError):
        decode_log_entry(b"\x55" + GOLDEN_ERROR_BYTES[1:])


def test_decode_rejects_truncated_record():
    with pytest.raises(LogCodecError):
        decode_log_entry(GOLDEN_ERROR_BYTES[:-1])
    with pytest.raises(LogCodecError):
        decode_log_entry(GOLDEN_ERROR_BYTES[:3])


def test_decode_stream_with_garbage_between_records():
    stream = b"\x00\x01" + GOLDEN_ERROR_BYTES + b"\xde\xad\xbe\xef" + GOLDEN_MSG_BYTES + b"\xa8"
    entries = decode_log_stream(stream)
    assert len(entries) == 2
    assert entries[0].err_code == 301
    assert entries[1].msg == "Hi"


def test_entry_to_text_error_code_with_timestamp():
    entry, _ = decode_log_entry(GOLDEN_ERROR_BYTES)
    text = entry_to_text(entry)
    path = file_path_from_id(7)
    assert text == f"25-01-01_00-00-00 ERROR -> {path}:123 - 301"


def test_entry_to_text_msg_without_timestamp():
    entry, _ = decode_log_entry(GOLDEN_MSG_BYTES)
    path = file_path_from_id(2)
    assert entry_to_text(entry) == f"DEBUG -> {path}:10 - Hi"


def test_entry_to_text_unknown_file_id():
    entry = LogEntry(level=3, is_msg=True, file_id=FILE_ID_UNKNOWN, line=5, msg="hello")
    assert entry_to_text(entry) == f"WARN  -> <file:{FILE_ID_UNKNOWN}>:5 - hello"


def test_file_id_mapping_round_trip():
    files = load_file_id_mapping()
    assert len(files) > 0
    for file_id, path in enumerate(files):
        assert file_path_from_id(file_id) == path
        assert file_id_from_path(path) == file_id
    assert file_id_from_path("not/a/real/file.c") == FILE_ID_UNKNOWN
    assert file_path_from_id(FILE_ID_UNKNOWN) is None


@pytest.mark.parametrize(
    "line",
    [
        "25-01-01_00-00-00 ERROR -> obc/app/modules/logger/logger.c:123 - 301",
        "DEBUG -> obc/app/modules/logger/logger.c:10 - Starting init",
        "25-06-09_14-30-01 INFO  -> obc/app/sys/print/obc_print.c:42 - Executing log downlink command",
    ],
)
def test_parse_text_then_encode_decode_round_trip(line):
    """Existing text logs can be encoded to binary and decoded back unchanged."""
    parsed = parse_text_log_line(line)
    encoded = encode_log_entry(parsed)
    decoded, _ = decode_log_entry(encoded)
    assert entry_to_text(decoded) == line


def test_parse_unix_style_text_round_trip():
    """LOG_UNIX-style lines round-trip when rendered with unix_style=True."""
    line = "1735689600 ERROR -> obc/app/modules/logger/logger.c:123 - 301"
    parsed = parse_text_log_line(line)
    decoded, _ = decode_log_entry(encode_log_entry(parsed))
    assert entry_to_text(decoded, unix_style=True) == line


def test_parse_text_log_line_fields():
    entry = parse_text_log_line("25-01-01_00-00-00 ERROR -> obc/app/modules/logger/logger.c:123 - 301\r\n")
    assert entry.level_name == "ERROR"
    assert entry.is_msg is False
    assert entry.err_code == 301
    assert entry.line == 123
    assert entry.timestamp == TS_2025_01_01
    assert entry.file_path == "obc/app/modules/logger/logger.c"
    assert entry.file_id == file_id_from_path("obc/app/modules/logger/logger.c")
    assert entry.file_id != FILE_ID_UNKNOWN


def test_parse_text_log_line_unknown_path():
    entry = parse_text_log_line("WARN -> some/unknown/file.c:9 - watch out")
    assert entry.file_id == FILE_ID_UNKNOWN
    assert entry.file_path == "some/unknown/file.c"
    assert entry.is_msg is True
    assert entry.msg == "watch out"
    assert entry.timestamp is None


def test_parse_text_log_line_invalid():
    with pytest.raises(LogCodecError):
        parse_text_log_line("this is not a log line")


def test_binary_is_smaller_than_text():
    """Sanity check the point of the whole exercise: binary records are much smaller."""
    text = "25-01-01_00-00-00 ERROR -> obc/app/modules/logger/logger.c:123 - 301\r\n"
    entry = parse_text_log_line(text)
    encoded = encode_log_entry(entry)
    assert len(encoded) < len(text) / 4
