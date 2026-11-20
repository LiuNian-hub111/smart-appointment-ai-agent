"""Unambiguous booking messages avoid a remote classification call."""

from agents.task_classification.intent_rules import classify_obvious_intent


def test_explicit_booking_is_classified_locally():
    assert classify_obvious_intent("我想预约2026年12月1日下午3点的高中力学课") == "appointment"
    assert classify_obvious_intent("请帮我约课，明天下午三点") == "appointment"


def test_questions_and_ambiguous_messages_still_use_model():
    assert classify_obvious_intent("怎么预约物理课？") is None
    assert classify_obvious_intent("预约一节物理课多少钱？") is None
    assert classify_obvious_intent("我想了解老师的情况") is None
