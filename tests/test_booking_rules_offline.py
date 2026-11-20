"""Boundary checks for local parsing of explicit lesson requests."""

from agents.appointment.booking_rules import parse_explicit_booking


def test_complete_demo_booking_is_parsed_without_model():
    data = parse_explicit_booking("我想预约演示老师B在2026年12月4日下午3点的高中物理电磁学课，上60分钟。")
    assert data["start_time"] == "2026-12-04 15:00"
    assert data["duration"] == "60分钟"
    assert data["project"] == "高中物理电磁学"
    assert data["teacher_name"] == "演示老师B"
    assert data["info_complete"] is True


def test_explicit_half_hour_and_combined_duration():
    data = parse_explicit_booking("2026-12-04 下午3点半约高中力学课，上1小时30分钟")
    assert data["start_time"] == "2026-12-04 15:30"
    assert data["duration"] == "90分钟"


def test_uncertain_or_missing_details_fall_back_to_model():
    assert parse_explicit_booking("明天下午3点约高中力学课，上60分钟") is None
    assert parse_explicit_booking("2026年12月4日下午3点左右约高中力学课，上60分钟") is None
    assert parse_explicit_booking("2026年12月4日下午3点约张老师的高中力学课，上60分钟") is None
    assert parse_explicit_booking("2026年12月4日下午3点约高中力学课") is None
    assert parse_explicit_booking("2026年12月4日15:00或17:00约高中力学课，上60分钟") is None
