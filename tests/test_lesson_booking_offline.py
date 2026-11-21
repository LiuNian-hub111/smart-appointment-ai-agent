"""Offline checks for the education booking changes."""

from datetime import datetime, timedelta
import json
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import sqlite3
from threading import Event

import pytest

from agents.appointment.appointment_processor import AppointmentProcessor
from agents.appointment.message_builder import MessageBuilder
from db.db_router import DatabaseRouter


def test_browser_prepares_card_without_saving_booking():
    from config.booking_context import prepare_booking
    processor = object.__new__(AppointmentProcessor)
    start = datetime(2026, 12, 6, 15)
    processor.teacher_finder = SimpleNamespace(
        parse_time_and_duration=lambda *_: (start, start + timedelta(hours=1), 60)
    )
    # No database component: any attempted save would fail this test.
    setting = prepare_booking.set(True)
    try:
        operation = processor._process_successful_appointment(
            {"id": 1, "name": "演示老师A"},
            {"start_time": "2026-12-06 15:00", "duration": "60分钟", "project": "物理"}, "demo"
        )
        with pytest.raises(StopIteration) as result:
            operation.send(None)
        proposal = result.value.value.split("[BOOKING]", 1)[1].split("[REPLY]", 1)[0]
        assert json.loads(proposal)["teacher_id"] == 1
        assert "成功" not in result.value.value
    finally:
        prepare_booking.reset(setting)


def test_lesson_details_are_complete_without_teacher_gender():
    processor = object.__new__(AppointmentProcessor)
    history = {}

    complete = processor.update_history_from_data(
        history,
        {"start_time": "2026-12-01 15:00", "project": "高中力学", "duration": "90分钟"},
    )

    assert complete is True
    assert history == {
        "start_time": "2026-12-01 15:00",
        "project": "高中力学",
        "duration": "90分钟",
    }
    assert "性别" not in MessageBuilder().create_missing_info_questions(["project"])


def test_same_teacher_cannot_be_booked_twice_for_overlapping_times(tmp_path):
    database = DatabaseRouter(f"sqlite:///{(tmp_path / 'lessons.db').as_posix()}")
    try:
        teacher_id = database.teachers.add_teacher("演示老师", None, "高中物理力学")
        start = datetime(2026, 12, 1, 15, 0)
        end = start + timedelta(minutes=90)
        database.teachers.add_schedule(teacher_id, start, end, "busy", 1)

        with pytest.raises(ValueError, match="已有课程"):
            database.teachers.add_schedule(
                teacher_id, start + timedelta(minutes=30), end + timedelta(minutes=30), "busy", 2
            )

        assert len(database.teachers.get_teacher_schedules(teacher_id, start)) == 1
    finally:
        database.close()


def test_simultaneous_booking_waits_then_rechecks_conflict(tmp_path):
    db_file = tmp_path / "concurrent_lessons.db"
    database = DatabaseRouter(f"sqlite:///{db_file.as_posix()}")
    start = datetime(2026, 12, 5, 15, 0)
    end = start + timedelta(minutes=60)
    teacher_id = database.teachers.add_teacher("演示老师", None, "高中物理")
    writer = sqlite3.connect(db_file)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute(
        "INSERT INTO teacher_schedules (teacher_id, start_time, end_time, status, appointment_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (teacher_id, str(start), str(end), "busy", 1),
    )
    started = Event()

    def competing_booking():
        started.set()
        return database.teachers.add_schedule(teacher_id, start, end, "busy", 2)

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(competing_booking)
            assert started.wait(timeout=2)
            with pytest.raises(TimeoutError):
                future.result(timeout=0.2)
            writer.commit()
            with pytest.raises(ValueError, match="已有课程"):
                future.result(timeout=5)
        assert len(database.teachers.get_teacher_schedules(teacher_id, start)) == 1
    finally:
        writer.close()
        database.close()
