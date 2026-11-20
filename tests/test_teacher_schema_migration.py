"""Existing local bookings survive the teacher-domain schema rename."""

import sqlite3
from datetime import datetime

from db.db_router import DatabaseRouter


def test_existing_booking_survives_teacher_schema_migration(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE technicians (id INTEGER PRIMARY KEY, name TEXT, gender TEXT, strength TEXT)"
        )
        connection.execute(
            "CREATE TABLE technician_schedules (id INTEGER PRIMARY KEY, technician_id INTEGER, "
            "start_time DATETIME, end_time DATETIME, status TEXT, appointment_id INTEGER)"
        )
        connection.execute(
            "INSERT INTO technicians VALUES (1, '演示老师A', NULL, '高中力学')"
        )
        connection.execute(
            "INSERT INTO technician_schedules VALUES "
            "(1, 1, '2026-12-01 15:00:00', '2026-12-01 16:30:00', 'busy', 42)"
        )

    database = DatabaseRouter(f"sqlite:///{path.as_posix()}")
    try:
        assert database.teachers.get_teacher_by_id(1)["name"] == "演示老师A"
        assert not database.teachers.is_teacher_available(
            1, datetime(2026, 12, 1, 15, 30), datetime(2026, 12, 1, 16, 30)
        )
    finally:
        database.close()

    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "teachers" in tables
        assert "teacher_schedules" in tables
        assert "technicians" not in tables
        assert "technician_schedules" not in tables


def test_fresh_database_uses_teacher_tables(tmp_path):
    path = tmp_path / "fresh.db"
    database = DatabaseRouter(f"sqlite:///{path.as_posix()}")
    database.close()
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "teachers" in tables
        assert "teacher_schedules" in tables
