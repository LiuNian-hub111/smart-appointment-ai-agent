import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest
from langchain_core.chat_history import InMemoryChatMessageHistory
from config.constants import SharedState, StateEnum
from services.conversation_memory import (
    ConversationMemoryRepository, snapshot_agent, restore_agent, memory_command,
)
from services.conversation_store import ConversationStore


def agent_factory(key):
    state = SharedState()
    return SimpleNamespace(
        state_manager=SimpleNamespace(state=state, get_current_state=lambda: state.value),
        appointment_agent=SimpleNamespace(appointment_history={}, finished=False,
                                         chat_history=InMemoryChatMessageHistory()),
    )


def test_restart_restores_progress_and_explicit_preference(tmp_path):
    path = f"sqlite:///{(tmp_path / 'memory.db').as_posix()}"
    key, other = str(uuid4()), str(uuid4())
    async def run():
        repo = ConversationMemoryRepository(path)
        store = ConversationStore(agent_factory, repository=repo, snapshot=snapshot_agent, restore=restore_agent)
        async with store.open(key) as agent:
            agent.state_manager.state.value = StateEnum.APPOINTMENT
            agent.appointment_agent.appointment_history = {
                'start_time': '2026-12-12 15:00', 'project': '力学',
                'awaiting_confirmation': True, 'recommended_teacher': {'id': 2, 'name': '老师B'},
            }
            agent.appointment_agent.chat_history.add_user_message('周六上力学课')
            memory_command(agent, '记住课程偏好：高中物理力学')
        repo.close()
        # Discard all objects, then reopen the file as a fresh server would.
        repo = ConversationMemoryRepository(path)
        store = ConversationStore(agent_factory, repository=repo, snapshot=snapshot_agent, restore=restore_agent)
        async with store.open(key) as agent:
            assert agent.state_manager.state.value == StateEnum.APPOINTMENT
            assert agent.appointment_agent.appointment_history['recommended_teacher']['id'] == 2
            assert agent.appointment_agent.chat_history.messages[0].content == '周六上力学课'
            assert '高中物理力学' in memory_command(agent, '查看记忆')
            memory_command(agent, '忘记课程偏好')
        async with store.open(other) as agent:
            assert agent.appointment_agent.appointment_history == {}
            assert agent.remembered_preferences == {}
        repo.close()
        repo = ConversationMemoryRepository(path)
        assert repo.load(key)['preferences'] == {}
        assert repo.load(key)['appointment']['project'] == '力学'
        repo.close()
    asyncio.run(run())


def test_failed_turn_does_not_overwrite_saved_memory(tmp_path):
    repo = ConversationMemoryRepository(f"sqlite:///{(tmp_path / 'failure.db').as_posix()}")
    key = str(uuid4())
    async def run():
        store = ConversationStore(agent_factory, repository=repo, snapshot=snapshot_agent, restore=restore_agent)
        async with store.open(key) as agent:
            memory_command(agent, '记住课程偏好：力学')
        with pytest.raises(RuntimeError):
            async with store.open(key) as agent:
                memory_command(agent, '记住课程偏好：错误修改')
                raise RuntimeError('turn failed')
        async with store.open(key) as agent:
            assert agent.remembered_preferences['course'] == '力学'
        assert repo.load(key)['preferences']['course'] == '力学'
    asyncio.run(run())
    repo.close()


def test_user_memory_crosses_chats_and_survives_restart_without_progress_leak(tmp_path, monkeypatch):
    path = f"sqlite:///{(tmp_path / 'user_memory.db').as_posix()}"
    spec = importlib.util.spec_from_file_location('memory_chat_handler', Path(__file__).resolve().parents[1] / 'api' / 'chat_handler.py')
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)
    repo = ConversationMemoryRepository(path)
    store = ConversationStore(agent_factory, repository=repo, snapshot=snapshot_agent, restore=restore_agent)
    monkeypatch.setattr(handler, 'profile_repository', repo)
    monkeypatch.setattr(handler, 'conversations', store)
    a, b = str(uuid4()), str(uuid4())
    async def send(key, text):
        return ''.join([token async for token in handler.ProcessUserInput_stream(text, conversation_id=key)])
    async def first_run():
        assert '已记住' in await send(a, '记住课程偏好：力学')
        async with store.open(a) as agent:
            agent.appointment_agent.appointment_history = {'start_time': '2026-12-12 15:00'}
        assert '力学' in await send(b, '查看记忆')
        async with store.open(b) as agent:
            assert agent.appointment_agent.appointment_history == {}
        assert repo.load_preferences('another-user') == {}
    asyncio.run(first_run())
    repo.close()
    repo = ConversationMemoryRepository(path)
    store = ConversationStore(agent_factory, repository=repo, snapshot=snapshot_agent, restore=restore_agent)
    monkeypatch.setattr(handler, 'profile_repository', repo)
    monkeypatch.setattr(handler, 'conversations', store)
    async def second_run():
        assert '力学' in await send(str(uuid4()), '查看记忆')
        await send(b, '记住课程偏好：电磁学')
        assert '电磁学' in await send(a, '查看记忆')
        await send(a, '忘记课程偏好')
        assert '暂无' in await send(b, '查看记忆')
        assert repo.load_preferences(handler.DEMO_USER_ID) == {}
    asyncio.run(second_run())
    repo.close()
