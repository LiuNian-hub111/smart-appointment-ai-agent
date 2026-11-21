"""Fast classification for unambiguous booking requests."""
from services.automatic_memory import learning_statement


def classify_obvious_intent(task: str) -> str | None:
    text = "".join(task.split())
    if not text:
        return None
    if learning_statement(task):
        return 'query'

    # Questions about price or the booking process are consultations, even
    # when they contain the word "预约".
    if any(word in text for word in ("多少钱", "价格", "收费", "费用", "怎么", "如何", "流程")):
        return None

    if any(
        phrase in text
        for phrase in (
            "我想预约", "我要预约", "帮我预约", "请预约", "我想约课", "我要约课", "帮我约课", "请帮我约课"
        )
    ):
        return "appointment"

    return None
