"""Browser chats prepare a booking; only the confirmation API persists it."""
from contextvars import ContextVar

prepare_booking = ContextVar("prepare_booking", default=False)
