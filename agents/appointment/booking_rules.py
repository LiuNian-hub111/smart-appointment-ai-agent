"""Parse fully specified demo lesson requests without a remote model call."""

import re
from datetime import datetime


COURSE_TOPICS = (
    "高中物理电磁学", "高中物理力学", "高中电磁学", "高中力学", "物理辅导", "物理课"
)


def parse_explicit_booking(message: str) -> dict | None:
    """Return appointment fields only when every required detail is explicit."""
    date_match = re.search(r"(?<!\d)(\d{4})[-年](\d{1,2})[-月](\d{1,2})(?:日)?", message)
    if not date_match:
        return None
    if any(word in message for word in ("左右", "大概", "可能")):
        return None

    time_matches = list(re.finditer(
        r"(上午|下午|晚上|中午|凌晨)?\s*(\d{1,2})(?:[:：]([0-5]\d)|点(?:(半)|([0-5]?\d)分?)?|时(?:(\d{1,2})分?)?)",
        message[date_match.end():],
    ))
    duration_match = re.search(r"(?<!\d)(\d{1,3})\s*分钟", message)
    hour_duration_match = re.search(r"(?<![\d.])(\d{1,2})\s*小时", message)
    topics = [topic for topic in COURSE_TOPICS if topic in message]
    if len(time_matches) != 1 or not topics or not (duration_match or hour_duration_match):
        return None

    try:
        year, month, day = map(int, date_match.groups())
        time_match = time_matches[0]
        period, hour_text, colon_minute, half, point_minute, hour_minute = time_match.groups()
        hour = int(hour_text)
        minute = int(colon_minute or point_minute or hour_minute or ("30" if half else "0"))
        if period in ("下午", "晚上") and hour < 12:
            hour += 12
        elif period in ("上午", "凌晨") and hour == 12:
            hour = 0
        start = datetime(year, month, day, hour, minute)
    except ValueError:
        return None

    duration = int(hour_duration_match.group(1)) * 60 if hour_duration_match else 0
    duration += int(duration_match.group(1)) if duration_match else 0
    if duration < 15 or duration > 240:
        return None

    teacher_match = re.search(r"演示老师[A-C]", message)
    if "老师" in message and teacher_match is None:
        return None
    return {
        "start_time": start.strftime("%Y-%m-%d %H:%M"),
        "duration": f"{duration}分钟",
        "project": max(topics, key=len),
        "preference": "无",
        "teacher_name": teacher_match.group(0) if teacher_match else "未知",
        "confirmation": "未知",
        "info_complete": True,
        "unrelated": False,
        "missing_info": [],
    }
