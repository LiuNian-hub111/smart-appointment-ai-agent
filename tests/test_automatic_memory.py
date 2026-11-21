import asyncio
import json
from types import SimpleNamespace
from services.automatic_memory import extract, validate_changes, quick_command, learning_statement
from services.conversation_memory import ConversationMemoryRepository


class FakeModel:
    def __init__(self, changes):
        self.changes = changes
    async def ainvoke(self, messages):
        return SimpleNamespace(content=json.dumps({'changes': self.changes}))


def test_semantic_extraction_and_stable_update():
    text = '我的力学基础比较差，平时只有周末有时间'
    items = [dict(key='learning_need', value='力学基础薄弱', evidence='我的力学基础比较差'),
             dict(key='availability', value='通常周末方便', evidence='平时只有周末有时间')]
    result = asyncio.run(extract(text, FakeModel(items)))
    assert result == {'learning_need': '力学基础薄弱', 'availability': '通常周末方便'}
    result = asyncio.run(extract('我现在周末没空了', FakeModel([
        dict(key='availability', value='周末不方便', evidence='我现在周末没空了')
    ])))
    assert result['availability'] == '周末不方便'


def test_temporary_third_party_and_unsupported_fields_are_not_stored():
    for text in ('我这周六有空', '我帮朋友问，他力学很差', '假如我周末有空'):
        assert validate_changes({'changes': [dict(key='availability', value='周末方便', evidence=text)]}, text) == {}
    text = '我的力学基础不好'
    assert validate_changes({'changes': [dict(key='password', value='secret', evidence=text),
                                        dict(key='course', value='力学', evidence='不存在的依据')]}, text) == {}


def test_natural_forget_view_and_selective_delete(tmp_path):
    assert quick_command('忘记偏好') == 'forget'
    assert quick_command('你还记得我什么？') == 'view'
    assert quick_command('忘记我的时间偏好') == 'forget:availability'
    repo = ConversationMemoryRepository(f"sqlite:///{(tmp_path / 'auto.db').as_posix()}")
    repo.patch_preferences('user', {'course': '力学', 'availability': '周末方便'})
    assert repo.patch_preferences('user', {'availability': None}) == {'course': '力学'}
    assert repo.load_preferences('other') == {}
    repo.close()


def test_failed_model_does_not_create_memory():
    class Broken:
        async def ainvoke(self, messages):
            raise RuntimeError('unavailable')
    assert asyncio.run(extract('我物理基础不好', Broken())) == {}


def test_explicit_learning_difficulties_have_grounded_local_fallback():
    for text in ('我的电磁学不太明白', '我不太懂电场', '我的力学基础比较差', '我电磁感应学不会'):
        # The last phrasing remains outside the intentionally limited local parser.
        if text.endswith('学不会'):
            assert learning_statement(text) is None
        else:
            assert asyncio.run(extract(text)) == {'learning_need': text}
    for text in ('我朋友的电磁学不太明白', '这次电磁学不太明白',
                 '我的电磁学不太明白，帮我预约明天的课', '我的电磁学不太明白吗？'):
        assert learning_statement(text) is None


def test_learning_statement_handler_remembers_and_responds_without_model(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    from uuid import uuid4
    from services.conversation_store import ConversationStore
    spec = importlib.util.spec_from_file_location('learning_chat_handler', Path(__file__).resolve().parents[1] / 'api' / 'chat_handler.py')
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)
    repo = ConversationMemoryRepository(f"sqlite:///{(tmp_path / 'learning.db').as_posix()}")
    monkeypatch.setattr(handler, 'profile_repository', repo)
    monkeypatch.setattr(handler, 'conversations', ConversationStore(lambda key: SimpleNamespace()))
    async def run():
        replies = ''.join([part async for part in handler.ProcessUserInput_stream('我的电磁学不太明白', conversation_id=str(uuid4()))])
        assert '不支持' not in replies
        assert '哪个知识点' in replies
        assert repo.load_preferences(handler.DEMO_USER_ID)['learning_need'] == '我的电磁学不太明白'
    asyncio.run(run())
    repo.close()
