"""Idempotent confirmation for the local SQLite demo (one shared user)."""

import json
from sqlalchemy import text
from db.db_router import DatabaseRouter
from db.models import BookingRequest, Teacher, TeacherSchedule


class BookingConflict(ValueError):
    pass


class BookingService:
    def __init__(self, database: DatabaseRouter):
        self.database = database

    def confirm(self, request_id, teacher_id, start_time, end_time, course):
        if start_time >= end_time:
            raise ValueError("结束时间必须晚于开始时间")
        payload = json.dumps({
            "teacher_id": teacher_id, "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(), "course": course,
        }, ensure_ascii=False, sort_keys=True)
        with self.database.session_manager.session_scope() as session:
            if session.bind.dialect.name != "sqlite":
                raise RuntimeError("此确认接口目前仅支持 SQLite")
            session.execute(text("BEGIN IMMEDIATE"))
            previous = session.get(BookingRequest, request_id)
            if previous is not None:
                if previous.payload != payload:
                    raise BookingConflict("请求编号已用于其他约课内容，请使用新编号")
                return dict(previous.result)
            if session.get(Teacher, teacher_id) is None:
                raise LookupError("老师不存在")
            conflict = session.query(TeacherSchedule).filter(
                TeacherSchedule.teacher_id == teacher_id,
                TeacherSchedule.status == "busy",
                TeacherSchedule.start_time < end_time,
                TeacherSchedule.end_time > start_time,
            ).first()
            if conflict is not None:
                raise BookingConflict("老师在该时间段已有课程")
            schedule = TeacherSchedule(
                teacher_id=teacher_id, start_time=start_time, end_time=end_time,
                status="busy",
            )
            session.add(schedule)
            session.flush()
            result = {
                "request_id": request_id, "schedule_id": schedule.id,
                "teacher_id": teacher_id, "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(), "course": course, "status": "busy",
            }
            session.add(BookingRequest(
                request_id=request_id, payload=payload,
                schedule_id=schedule.id, result=result,
            ))
            # session_scope commits both records before the caller receives this.
            return result
