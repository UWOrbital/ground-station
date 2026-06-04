import pytest
from datetime import datetime
from sqlmodel import Session
from data.resources.commands_pipeline import CommandsPipeline
from data.tables.main_tables import MainCommand
from data.tables.transactional_tables import Commands
from data.enums.transactional import CommandStatus
from data.data_wrappers.wrappers import CommandsWrapper

@pytest.fixture
def pipeline():
    return CommandsPipeline()

def test_build_queue_integration(db_session: Session, pipeline: CommandsPipeline):
    # 1. Setup MainCommands (one high prio, one low prio)
    # Using valid CmdCallbackId values from the enum (e.g. 2 for RTC_SYNC, 3 for DOWNLINK_LOGS)
    mc_high = MainCommand(id=3, name="DownlinkLogs", data_size=1, total_size=1, priority=10)
    mc_low = MainCommand(id=2, name="RtcSync", data_size=1, total_size=1, priority=1)
    db_session.add(mc_high)
    db_session.add(mc_low)
    db_session.flush()

    # 2. Setup Commands (Pending)
    # Valid parameter names based on CLICommand logic: log_level, time_of_execution
    cmd_low = Commands(type_=mc_low.id, params="rtc_time,12345678", status=CommandStatus.PENDING)
    cmd_high = Commands(type_=mc_high.id, params="log_level,1,time_of_execution,0", status=CommandStatus.PENDING)
    db_session.add(cmd_low)
    db_session.add(cmd_high)
    db_session.flush()

    # 3. Build Queue
    pipeline.build_queue()

    # 4. Verify queue population and sorting (asc by prio)
    assert len(pipeline.commands_queue) == 2
    assert pipeline.commands_queue[0].command.id == cmd_low.id
    assert pipeline.commands_queue[1].command.id == cmd_high.id

    # 5. Verify database status updates
    db_session.refresh(cmd_low)
    db_session.refresh(cmd_high)
    assert cmd_low.status == CommandStatus.SCHEDULED
    assert cmd_high.status == CommandStatus.SCHEDULED

def test_queue_to_packet_integration(db_session: Session, pipeline: CommandsPipeline, monkeypatch):
    # Setup
    mc = MainCommand(id=5, name="Ping", data_size=1, total_size=1, priority=1)
    db_session.add(mc)
    db_session.flush()

    cmd = Commands(type_=mc.id, params="", status=CommandStatus.PENDING)
    db_session.add(cmd)
    db_session.flush()

    pipeline.build_queue()

    monkeypatch.setattr("data.resources.commands_pipeline.command_multi_pack", lambda x: [b"packet_data"])
    monkeypatch.setattr("data.resources.commands_pipeline.CommandPackaging.encode_frame", lambda self, x: b"FRAME_" + x)

    packets = pipeline.queue_to_packet()

    assert len(packets) == 1
    assert b"FRAME_packet_data" in packets[0]

    # Verify status update in DB
    db_session.refresh(cmd)
    assert cmd.status == CommandStatus.ONGOING
