"""Interleaved chats must retain independent state without model calls."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from services.conversation_store import ConversationStore


def test_interleaved_handler_conversations_do_not_share_history(monkeypatch, tmp_path):
    source = Path(__file__).resolve().parents[1] / 'api' / 'chat_handler.py'
    spec = importlib.util.spec_from_file_location('isolated_chat_handler', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from services.conversation_memory import ConversationMemoryRepository
    profile = ConversationMemoryRepository(f"sqlite:///{(tmp_path / 'profile.db').as_posix()}")
    monkeypatch.setattr(module, 'profile_repository', profile)

    class FakeAgent:
        def __init__(self, key):
            self.history = []
            self.state_manager = SimpleNamespace(should_classify=lambda: False)
        async def classify_task_stream(self, message):
            self.history.append(message)
            yield '|'.join(self.history)

    store = ConversationStore(FakeAgent)
    monkeypatch.setattr(module, 'conversations', store)
    async def run():
        a, b = str(uuid4()), str(uuid4())
        async def send(key, message):
            return ''.join([token async for token in module.ProcessUserInput_stream(message, conversation_id=key)])
        assert await send(a, '周六力学') == '周六力学'
        assert await send(b, '周日电磁学') == '周日电磁学'
        assert await send(a, '下午三点') == '周六力学|下午三点'
        assert await send(b, '老师B') == '周日电磁学|老师B'
        # Starting a new chat has no old history.
        assert await send(str(uuid4()), '新对话') == '新对话'
    asyncio.run(run())
    profile.close()


def test_same_conversation_serializes_but_other_chat_can_proceed():
    async def run():
        store = ConversationStore(lambda key: {})
        a, b = str(uuid4()), str(uuid4())
        release, entered = asyncio.Event(), asyncio.Event()
        order = []
        async def first():
            async with store.open(a):
                entered.set()
                await release.wait()
                order.append('first')
        async def second():
            async with store.open(a):
                order.append('second')
        task = asyncio.create_task(first())
        await entered.wait()
        other = asyncio.create_task(second())
        async with store.open(b):
            assert order == []
        release.set()
        await asyncio.gather(task, other)
        assert order == ['first', 'second']
        assert not store.entries[a].lock.locked()
    asyncio.run(run())


def test_store_rejects_invalid_ids_and_limits_new_conversations():
    async def run():
        store = ConversationStore(lambda key: {}, limit=1)
        key = str(uuid4())
        async with store.open(key):
            pass
        with pytest.raises(ValueError):
            async with store.open('invalid'):
                pass
        with pytest.raises(RuntimeError, match='上限'):
            async with store.open(str(uuid4())):
                pass
        async with store.open(key):
            pass
    asyncio.run(run())
