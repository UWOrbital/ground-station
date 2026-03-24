import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import warnings

from data.resources.commands_pipeline import CommandsPipeline

@pytest.fixture
def pipeline():
    return CommandsPipeline()

def create_mock_command(prio: int, time_offset_seconds: int = 0):
    cmd = MagicMock()
    cmd.prio = prio
    cmd.time = datetime.now() + timedelta(seconds=time_offset_seconds)
    cmd.cmd_msg = MagicMock()
    return cmd

def test_initialization(pipeline):
    assert pipeline.commands_queue == []
    assert pipeline.packet_list == []



def test_sort_queue_by_priority(pipeline):
    cmd_low_prio = create_mock_command(prio=2)
    cmd_high_prio = create_mock_command(prio=1)

    pipeline.commands_queue = [cmd_low_prio, cmd_high_prio]
    sorted_queue = pipeline.sort_queue()

    assert sorted_queue == [cmd_high_prio, cmd_low_prio]

def test_sort_queue_by_time_when_same_priority(pipeline):
    cmd_old = create_mock_command(prio=1, time_offset_seconds=-10)
    cmd_new = create_mock_command(prio=1, time_offset_seconds=10)

    pipeline.commands_queue = [cmd_new, cmd_old]
    sorted_queue = pipeline.sort_queue()

    assert sorted_queue == [cmd_old, cmd_new]

def test_sort_queue_mixed(pipeline):
    cmd_prio1_new = create_mock_command(prio=1, time_offset_seconds=10)
    cmd_prio1_old = create_mock_command(prio=1, time_offset_seconds=-10)
    cmd_prio2_new = create_mock_command(prio=2, time_offset_seconds=10)
    cmd_prio2_old = create_mock_command(prio=2, time_offset_seconds=-10)

    pipeline.commands_queue = [cmd_prio2_new, cmd_prio1_new, cmd_prio2_old, cmd_prio1_old]
    sorted_queue = pipeline.sort_queue()

    assert sorted_queue == [cmd_prio1_old, cmd_prio1_new, cmd_prio2_old, cmd_prio2_new]

@patch("data.resources.commands_pipeline.CommandsWrapper")
def test_clear_queue(mock_wrapper, pipeline):
    cmd = create_mock_command(prio=1)
    pipeline.commands_queue = [cmd]

    pipeline.clear_queue()
    assert pipeline.commands_queue == []

def test_clear_packets(pipeline):
    pipeline.packet_list = [b"pack1"]
    pipeline.clear_packets()
    assert pipeline.packet_list == []


@patch("data.resources.commands_pipeline.CommandsWrapper")
@patch("data.resources.commands_pipeline.PADDING_REQUIRED", 20)
@patch("data.resources.commands_pipeline.command_multi_pack")
@patch("data.resources.commands_pipeline.CommandPackaging")
def test_queue_to_packet(mock_command_packaging_class, mock_command_multi_pack, mock_wrapper, pipeline):
    cmd1 = create_mock_command(prio=1)
    cmd2 = create_mock_command(prio=2)
    pipeline.commands_queue = [cmd1, cmd2]

    mock_command_multi_pack.return_value = [b"pack1", b"pack2"]

    mock_comms_instance = MagicMock()
    mock_comms_instance.encode_frame.side_effect = lambda x: b"HEAD_" + x
    mock_command_packaging_class.return_value = mock_comms_instance

    packets = pipeline.queue_to_packet()

    mock_command_multi_pack.assert_called_once_with([cmd1.cmd_msg, cmd2.cmd_msg])
    assert mock_comms_instance.encode_frame.call_count == 2

    expected_packet1 = b"HEAD_pack1".ljust(20, b"\x00")
    expected_packet2 = b"HEAD_pack2".ljust(20, b"\x00")

    assert pipeline.packet_list == [expected_packet1, expected_packet2]
    assert packets == [expected_packet1, expected_packet2]
