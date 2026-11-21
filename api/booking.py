"""Structured lesson confirmation; retries reuse the same request ID."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from db.db_router import DatabaseRouter
from services.booking_service import BookingConflict, BookingService

router = APIRouter(prefix="/api/bookings", tags=["约课确认"])


class BookingInput(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    teacher_id: int = Field(gt=0)
    start_time: datetime
    end_time: datetime
    course: str = Field(min_length=1, max_length=200)

    @field_validator("request_id", "course", mode="before")
    @classmethod
    def strip_required(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("start_time", "end_time")
    @classmethod
    def local_time(cls, value):
        # Existing schedules use naive local China time.
        if value.tzinfo is not None:
            value = value.astimezone(timezone(timedelta(hours=8))).replace(tzinfo=None)
        return value

    @model_validator(mode="after")
    def valid_period(self):
        if self.end_time <= self.start_time:
            raise ValueError("结束时间必须晚于开始时间")
        return self


def get_booking_service():
    database = DatabaseRouter()
    try:
        yield BookingService(database)
    finally:
        database.close()


@router.post("/confirm")
def confirm_booking(item: BookingInput, service=Depends(get_booking_service)):
    try:
        return service.confirm(**item.model_dump())
    except BookingConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
