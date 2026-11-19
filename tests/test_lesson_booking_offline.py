"""Offline checks for the education booking changes."""

from datetime import datetime, timedelta

import pytest

from agents.appointment.appointment_processor import AppointmentProcessor
from agents.appointment.message_builder import MessageBuilder
from db.db_router import DatabaseRouter


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
        teacher_id = database.technicians.add_technician("演示老师", None, "高中物理力学")
        start = datetime(2026, 12, 1, 15, 0)
        end = start + timedelta(minutes=90)
        database.technicians.add_schedule(teacher_id, start, end, "busy", 1)

        with pytest.raises(ValueError, match="已有课程"):
            database.technicians.add_schedule(
                teacher_id, start + timedelta(minutes=30), end + timedelta(minutes=30), "busy", 2
            )

        assert len(database.technicians.get_technician_schedules(teacher_id, start)) == 1
    finally:
        database.close()
