"""Offline regression checks for the knowledge creation route."""

import importlib.util
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi import HTTPException
from pydantic import ValidationError


@pytest.fixture
def knowledge_module():
    source = Path(__file__).resolve().parents[1] / "api" / "knowledge.py"
    spec = importlib.util.spec_from_file_location("isolated_knowledge_api", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete_without_io(coroutine):
    """Drive a coroutine whose fake dependencies never suspend."""
    try:
        coroutine.send(None)
    except StopIteration as finished:
        return finished.value
    raise AssertionError("The offline route unexpectedly awaited external I/O")


def test_knowledge_item_rejects_empty_fields(knowledge_module):
    with pytest.raises(ValidationError):
        knowledge_module.KnowledgeItem(question="", answer="正常答案")
    with pytest.raises(ValidationError):
        knowledge_module.KnowledgeItem(question="正常问题", answer="")
    with pytest.raises(ValidationError):
        knowledge_module.KnowledgeItem(question="   ", answer="正常答案")
    with pytest.raises(ValidationError):
        knowledge_module.KnowledgeItem(question="正常问题", answer="   ")

    item = knowledge_module.KnowledgeItem(question=" 正常问题 ", answer=" 正常答案 ")
    assert item.question == "正常问题"
    assert item.answer == "正常答案"


def test_knowledge_item_accepts_free_content_but_rejects_blank_content(knowledge_module):
    with pytest.raises(ValidationError):
        knowledge_module.KnowledgeItem(content="   ")
    with pytest.raises(ValidationError):
        knowledge_module.KnowledgeItem()

    item = knowledge_module.KnowledgeItem(content=" 肩颈推拿 60 分钟 ", category="服务项目")
    assert item.content == "肩颈推拿 60 分钟"


def test_add_knowledge_passes_question_and_answer_to_service(knowledge_module, monkeypatch):
    calls = []

    class FakeKnowledgeService:
        initialized = False

        async def initialize(self):
            calls.append("initialize")
            self.initialized = True

        async def add_document(self, content, category):
            calls.append((content, category))
            return True

    fake_module = types.ModuleType("services.knowledge_service")
    fake_module.KnowledgeService = FakeKnowledgeService
    monkeypatch.setitem(sys.modules, "services.knowledge_service", fake_module)
    item = knowledge_module.KnowledgeItem(question="营业时间？", answer="9点到22点", category="营业时间")

    result = complete_without_io(knowledge_module.add_knowledge(item))

    assert result["status"] == "success"
    assert calls == ["initialize", ("问题: 营业时间？\n答案: 9点到22点", "营业时间")]


def test_free_content_add_and_update_reach_service(knowledge_module, monkeypatch):
    calls = []

    class FakeKnowledgeService:
        initialized = True

        async def add_document(self, **data):
            calls.append(("add", data))
            return True

        async def update_document(self, **data):
            calls.append(("update", data))
            return True

    fake_module = types.ModuleType("services.knowledge_service")
    fake_module.KnowledgeService = FakeKnowledgeService
    monkeypatch.setitem(sys.modules, "services.knowledge_service", fake_module)
    payload = {"content": " 肩颈推拿 60 分钟 ", "category": "服务项目", "keywords": ["肩颈", "推拿"]}
    item = knowledge_module.KnowledgeItem.model_validate(payload)

    assert complete_without_io(knowledge_module.add_knowledge(item))["status"] == "success"
    assert complete_without_io(knowledge_module.update_knowledge(7, item))["status"] == "success"
    assert calls == [
        ("add", {"content": "肩颈推拿 60 分钟", "category": "服务项目", "keywords": ["肩颈", "推拿"]}),
        ("update", {"doc_id": 7, "content": "肩颈推拿 60 分钟", "category": "服务项目", "keywords": ["肩颈", "推拿"]}),
    ]


def test_add_knowledge_reports_service_failure(knowledge_module, monkeypatch):
    class FailingKnowledgeService:
        initialized = True

        async def add_document(self, content, category):
            return False

    fake_module = types.ModuleType("services.knowledge_service")
    fake_module.KnowledgeService = FailingKnowledgeService
    monkeypatch.setitem(sys.modules, "services.knowledge_service", fake_module)
    item = knowledge_module.KnowledgeItem(question="营业时间？", answer="9点到22点")

    with pytest.raises(HTTPException) as error:
        complete_without_io(knowledge_module.add_knowledge(item))

    assert error.value.status_code == 500
    assert error.value.detail == "知识条目保存失败"


def test_knowledge_repository_persists_and_reads_document():
    from db.db_router import DatabaseRouter

    work_dir = Path(__file__).resolve().parents[2] / "work"
    with TemporaryDirectory(dir=work_dir) as temporary:
        database_url = "sqlite:///" + (Path(temporary) / "knowledge.db").as_posix()
        database = DatabaseRouter(db_path=database_url)
        document_id = database.knowledge.add_document("问题: 营业时间？\n答案: 9点到22点", "营业时间")
        document = database.knowledge.get_document(document_id)
        assert document["content"] == "问题: 营业时间？\n答案: 9点到22点"
        assert document["category"] == "营业时间"
        database.close()
