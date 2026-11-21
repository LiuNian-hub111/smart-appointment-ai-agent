"""Persist only serializable conversation state, never live agents or models."""
from langchain_core.messages import messages_to_dict, messages_from_dict
from db.base.session_manager import SessionManager
from db.models import ConversationMemory, UserMemory
from config.constants import StateEnum
from sqlalchemy import text as sql_text


class ConversationMemoryRepository:
    def __init__(self, db_path='sqlite:///data/smart_appointment.db'):
        self.db_path = db_path
        self._manager = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = SessionManager(self.db_path)
        return self._manager

    def load(self, key):
        with self.manager.session_scope() as session:
            record = session.get(ConversationMemory, key)
            return record.snapshot if record else None

    def save(self, key, snapshot):
        with self.manager.session_scope() as session:
            record = session.get(ConversationMemory, key)
            if record is None:
                session.add(ConversationMemory(conversation_id=key, snapshot=snapshot))
            else:
                record.snapshot = snapshot

    def close(self):
        if self._manager:
            self._manager.close()

    def load_preferences(self, user_id):
        with self.manager.session_scope() as session:
            record = session.get(UserMemory, user_id)
            return dict(record.preferences) if record else {}

    def save_preferences(self, user_id, preferences):
        with self.manager.session_scope() as session:
            record = session.get(UserMemory, user_id)
            if record is None:
                session.add(UserMemory(user_id=user_id, preferences=dict(preferences)))
            else:
                record.preferences = dict(preferences)

    def patch_preferences(self, user_id, changes):
        with self.manager.session_scope() as session:
            session.execute(sql_text('BEGIN IMMEDIATE'))
            record = session.get(UserMemory, user_id)
            values = dict(record.preferences) if record else {}
            for key, value in changes.items():
                if value is None:
                    values.pop(key, None)
                else:
                    values[key] = value
            if record:
                record.preferences = values
            else:
                session.add(UserMemory(user_id=user_id, preferences=values))
            return values


def snapshot_agent(agent):
    booking = agent.appointment_agent
    return {
        'version': 1,
        'state': agent.state_manager.get_current_state().value,
        'appointment': booking.appointment_history,
        'finished': booking.finished,
        'messages': messages_to_dict(booking.chat_history.messages[-40:]),
        'preferences': getattr(agent, 'remembered_preferences', {}),
    }


def restore_agent(agent, snapshot):
    if not snapshot:
        agent.remembered_preferences = {}
        return
    if snapshot.get('version') != 1:
        raise ValueError('不支持的会话记忆版本')
    agent.state_manager.state.value = StateEnum(snapshot['state'])
    booking = agent.appointment_agent
    booking.appointment_history = snapshot['appointment']
    booking.finished = snapshot['finished']
    booking.chat_history.clear()
    booking.chat_history.add_messages(messages_from_dict(snapshot['messages']))
    agent.remembered_preferences = snapshot.get('preferences', {})


def memory_command(agent, text, repository=None, user_id=None):
    """Explicit, user-controlled course preferences; never infer a booking time."""
    if repository is not None:
        agent.remembered_preferences = repository.load_preferences(user_id)
    preferences = getattr(agent, 'remembered_preferences', {})
    if text.strip() == '查看记忆':
        return '已记住的课程偏好：' + preferences.get('course', '暂无。')
    if text.strip() == '忘记课程偏好':
        if repository is not None:
            repository.save_preferences(user_id, {})
        agent.remembered_preferences = {}
        return '已忘记课程偏好。当前正在填写的预约信息不受影响。'
    prefix = '记住课程偏好：'
    if text.strip().startswith(prefix):
        course = text.strip()[len(prefix):].strip()
        if not course or len(course) > 100:
            return '请输入 1 到 100 字的课程偏好，例如：记住课程偏好：高中物理力学'
        if repository is not None:
            agent.remembered_preferences = repository.patch_preferences(user_id, {'course': course})
        else:
            agent.remembered_preferences = {**preferences, 'course': course}
        return '已记住课程偏好：' + course + '。填写约课时可用它作为默认课程，最终以确认卡片为准。'
    return None
