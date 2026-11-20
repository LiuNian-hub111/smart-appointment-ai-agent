"""Answer common course questions directly from the local knowledge base."""

from db.db_router import DatabaseRouter


def match_faq_category(question: str) -> str | None:
    text = question.strip()
    if not text:
        return None
    if any(word in text for word in ("多少钱", "价格", "收费", "费用", "学费")):
        return "课程价格"
    if any(word in text for word in ("怎么", "如何", "流程")) and any(
        word in text for word in ("约课", "预约", "报名")
    ):
        return "约课流程"
    return None


def answer_common_question(question: str, db_path: str = "sqlite:///data/smart_appointment.db") -> str | None:
    """Return current stored facts for a recognized FAQ, or None for Agent routing."""
    category = match_faq_category(question)
    if category is None:
        return None

    database = DatabaseRouter(db_path)
    try:
        documents = database.knowledge.search_documents_by_category(category)
        if not documents:
            return None
        return documents[0]["content"]
    finally:
        database.close()
