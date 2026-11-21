"""Persistent retry behavior without a model call or the live database."""

import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event

from db.db_router import DatabaseRouter
from db.models import BookingRequest, TeacherSchedule
from services.booking_service import BookingService


@pytest.fixture
def booking_api(tmp_path):
    database = DatabaseRouter(f"sqlite:///{(tmp_path / 'retry.db').as_posix()}")
    teacher_id = database.teachers.add_teacher("演示老师", strength="物理")
    source = Path(__file__).resolve().parents[1] / "api" / "booking.py"
    spec = importlib.util.spec_from_file_location("isolated_booking_api", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    app.dependency_overrides[module.get_booking_service] = lambda: BookingService(database)
    payload = dict(request_id="lesson-001", teacher_id=teacher_id,
                   start_time="2026-12-05T15:00:00", end_time="2026-12-05T16:00:00", course="高中物理")
    with TestClient(app) as client:
        yield database, client, payload
    database.close()


def test_retry_returns_persisted_result_and_one_booking(booking_api):
    db, client, payload = booking_api
    first = client.post("/api/bookings/confirm", json=payload)
    second = client.post("/api/bookings/confirm", json=payload)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    # A fresh engine/service must also find the saved receipt.
    other = DatabaseRouter(str(db.session_manager.engine.url))
    try:
        result = BookingService(other).confirm(
            **{**payload, "start_time": datetime.fromisoformat(payload["start_time"]),
               "end_time": datetime.fromisoformat(payload["end_time"])}
        )
        assert result == first.json()
    finally:
        other.close()
    with db.session_manager.session_scope() as session:
        assert session.query(TeacherSchedule).count() == 1
        assert session.query(BookingRequest).count() == 1


def test_reused_key_and_competing_new_key_are_conflicts(booking_api):
    db, client, payload = booking_api
    assert client.post("/api/bookings/confirm", json=payload).status_code == 200
    assert client.post("/api/bookings/confirm", json={**payload, "course": "力学"}).status_code == 409
    assert client.post("/api/bookings/confirm", json={**payload, "request_id": "other"}).status_code == 409


def test_invalid_request_creates_no_booking(booking_api):
    db, client, payload = booking_api
    for changes in ({"request_id": "  "}, {"course": "  "},
                    {"end_time": payload["start_time"]}):
        assert client.post("/api/bookings/confirm", json={**payload, **changes}).status_code == 422
    assert client.post("/api/bookings/confirm", json={**payload, "teacher_id": 999}).status_code == 404
    with db.session_manager.session_scope() as session:
        assert session.query(TeacherSchedule).count() == 0
        assert session.query(BookingRequest).count() == 0


def test_same_key_submitted_concurrently_has_one_result(booking_api):
    db, _, payload = booking_api
    barrier = Barrier(2)
    def submit():
        barrier.wait(timeout=5)
        return BookingService(db).confirm(
            **{**payload, "start_time": datetime.fromisoformat(payload["start_time"]),
               "end_time": datetime.fromisoformat(payload["end_time"])}
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert results[0] == results[1]
    with db.session_manager.session_scope() as session:
        assert session.query(TeacherSchedule).count() == 1
        assert session.query(BookingRequest).count() == 1


def test_failed_commit_rolls_back_receipt_and_booking_then_retry_works(booking_api):
    db, _, payload = booking_api
    kwargs = {**payload, "start_time": datetime.fromisoformat(payload["start_time"]),
              "end_time": datetime.fromisoformat(payload["end_time"])}
    session = db.session_manager.Session()
    def fail_commit(session):
        raise RuntimeError("simulated commit failure")
    event.listen(session, "before_commit", fail_commit)
    try:
        with pytest.raises(RuntimeError, match="commit failure"):
            BookingService(db).confirm(**kwargs)
    finally:
        event.remove(session, "before_commit", fail_commit)
    with db.session_manager.session_scope() as session:
        assert session.query(TeacherSchedule).count() == 0
        assert session.query(BookingRequest).count() == 0
    assert BookingService(db).confirm(**kwargs)["status"] == "busy"
