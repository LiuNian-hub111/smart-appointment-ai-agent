"""Common FAQ replies use saved knowledge without invoking a model."""

from db.db_router import DatabaseRouter
from services.common_faq import answer_common_question, match_faq_category


def test_only_common_consultations_use_fast_path():
    assert match_faq_category("高中物理辅导多少钱？") == "课程价格"
    assert match_faq_category("怎么预约物理课？") == "约课流程"
    assert match_faq_category("明天下午帮我预约物理课") is None


def test_common_faq_reads_current_database_content(tmp_path):
    db_path = f"sqlite:///{(tmp_path / 'faq.db').as_posix()}"
    database = DatabaseRouter(db_path)
    try:
        doc_id = database.knowledge.add_document("演示价格：60分钟100元", "课程价格")
        assert answer_common_question("物理课多少钱？", db_path) == "演示价格：60分钟100元"
        database.knowledge.update_document(doc_id, content="演示价格：60分钟120元")
        assert answer_common_question("物理课多少钱？", db_path) == "演示价格：60分钟120元"
        assert answer_common_question("怎么预约？", db_path) is None
    finally:
        database.close()
