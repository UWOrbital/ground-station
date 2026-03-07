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
    assert pipeline.lockout is False
    assert pipeline.commands_queue == []
    assert pipeline.packet_list == []

def test_add_to_queue_success(pipeline):
    cmd = create_mock_command(prio=1)
    status, queue = pipeline.add_to_queue(cmd)

    assert status is True
    assert len(queue) == 1
    assert queue[0] == cmd
    assert pipeline.commands_queue == queue

def test_add_to_queue_lockout(pipeline):
    pipeline.enable_lockout()
    assert pipeline.lockout is True

    cmd = create_mock_command(prio=1)
    with pytest.warns(UserWarning, match="Commands queue lockout active"):
        status, queue = pipeline.add_to_queue(cmd)

    assert status is False
    assert len(queue) == 0
    assert pipeline.commands_queue == []

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

def test_clear_queue(pipeline):
    cmd = create_mock_command(prio=1)
    pipeline.commands_queue = [cmd]

    cleared_queue = pipeline.clear_queue()
    assert cleared_queue == []
    assert pipeline.commands_queue == []


def test_disable_lockout(pipeline):
    pipeline.enable_lockout()
    assert pipeline.lockout is True
    pipeline.disable_lockout()
    assert pipeline.lockout is False


@patch("data.resources.commands_pipeline.PADDING_REQUIRED", 20)
@patch("data.resources.commands_pipeline.command_multi_pack")
@patch("data.resources.commands_pipeline.CommandPackaging")
def test_queue_to_packet(mock_command_packaging_class, mock_command_multi_pack, pipeline):
    cmd1 = create_mock_command(prio=1)
    cmd2 = create_mock_command(prio=2)
    pipeline.commands_queue = [cmd1, cmd2]

    mock_command_multi_pack.return_value = [b"pack1", b"pack2"]

    mock_comms_instance = MagicMock()
    mock_comms_instance.encode_frame.side_effect = lambda x: b"HEAD_" + x
    mock_command_packaging_class.return_value = mock_comms_instance

    pipeline.queue_to_packet()

    mock_command_multi_pack.assert_called_once_with([cmd1.cmd_msg, cmd2.cmd_msg])
    assert mock_comms_instance.encode_frame.call_count == 2

    expected_packet1 = b"HEAD_pack1".ljust(20, b"\x00")
    expected_packet2 = b"HEAD_pack2".ljust(20, b"\x00")

    assert pipeline.packet_list == [expected_packet1, expected_packet2]
