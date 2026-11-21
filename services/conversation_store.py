"""In-process conversation isolation for the local demo."""
import asyncio
from copy import deepcopy
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Conversation:
    agent: object
    lock: asyncio.Lock


class ConversationStore:
    def __init__(self, factory, limit=128, repository=None, snapshot=None, restore=None):
        self.factory = factory
        self.limit = limit
        self.entries = {}
        self.repository = repository
        self.snapshot = snapshot
        self.restore = restore

    @asynccontextmanager
    async def open(self, conversation_id):
        key = str(UUID(str(conversation_id)))
        # No await between lookup and insertion on the app event loop.
        if key not in self.entries:
            if len(self.entries) >= self.limit:
                raise RuntimeError('对话数量已达上限，请重启本地演示服务')
            agent = self.factory(key)
            if self.repository:
                self.restore(agent, self.repository.load(key))
            self.entries[key] = Conversation(agent, asyncio.Lock())
        entry = self.entries[key]
        async with entry.lock:
            previous = deepcopy(self.snapshot(entry.agent)) if self.repository else None
            try:
                yield entry.agent
                if self.repository:
                    self.repository.save(key, self.snapshot(entry.agent))
            except BaseException:
                # A failed or cancelled turn must not remain as unsaved state.
                if self.repository:
                    self.restore(entry.agent, previous)
                raise
