"""Route messages through independent conversation agents."""
import uuid
from services.automatic_memory import quick_command, describe, extract, memory_context
from services.conversation_store import ConversationStore
from services.conversation_memory import (
    ConversationMemoryRepository, snapshot_agent, restore_agent, memory_command,
)


def create_conversation(conversation_id):
    from agents.task_classification_agent import TaskClassificationAgent
    from agents.appointment_agent import AppointmentAgent
    from agents.consultant_agent import ConsultantAgent
    return TaskClassificationAgent(
        AppointmentAgent(session_id=conversation_id),
        ConsultantAgent(session_id=conversation_id),
    )


DEMO_USER_ID = 'local-demo-user'
profile_repository = ConversationMemoryRepository()

conversations = ConversationStore(
    create_conversation, repository=ConversationMemoryRepository(),
    snapshot=snapshot_agent, restore=restore_agent,
)


async def ProcessUserInput_stream(user_input, state=None, context=None, conversation_id=None):
    # Callers that omit an ID receive a fresh conversation, never a shared one.
    conversation_id = conversation_id or str(uuid.uuid4())
    async with conversations.open(conversation_id) as task_agent:
        command = quick_command(user_input)
        if command and command.startswith('forget:'):
            task_agent.remembered_preferences = profile_repository.patch_preferences(DEMO_USER_ID, {command.split(':')[1]: None})
            yield '[REPLY][咨询机器人]已忘记对应偏好。' + describe(task_agent.remembered_preferences)
            return
        if command == 'forget':
            profile_repository.save_preferences(DEMO_USER_ID, {})
            task_agent.remembered_preferences = {}
            yield '[REPLY][咨询机器人]已清除演示账号的偏好和学习需求记忆，当前预约信息不受影响。'
            return
        if command == 'view':
            yield '[REPLY][咨询机器人]' + describe(profile_repository.load_preferences(DEMO_USER_ID))
            return
        # The server chooses the demo identity; client-supplied IDs are not login.
        command_reply = memory_command(
            task_agent, user_input, repository=profile_repository, user_id=DEMO_USER_ID,
        )
        if command_reply is not None:
            yield f'[REPLY][咨询机器人]{command_reply}'
            return
        changes = await extract(user_input)
        if changes:
            task_agent.remembered_preferences = profile_repository.patch_preferences(DEMO_USER_ID, changes)
            yield '[REPLY][咨询机器人]已根据你这次的话更新记忆。' + describe(task_agent.remembered_preferences) + '。你可以随时说“忘记偏好”。\n'
            if not any(cue in user_input for cue in ('?', '？', '吗', '怎么', '为什么', '预约', '约课', '上课', '咨询', '推荐', '安排')):
                if changes.get('learning_need'):
                    yield '[REPLY][咨询机器人]你具体在哪个知识点遇到困难？可以举一道题，或说说想补习的内容。'
                return
        course = getattr(task_agent, 'remembered_preferences', {}).get('course')
        booking = getattr(task_agent, 'appointment_agent', None)
        if course and booking and not booking.appointment_history.get('project'):
            booking.appointment_history['project'] = course
        if task_agent.state_manager.should_classify():
            from services.common_faq import answer_common_question
            faq_answer = answer_common_question(user_input)
            if faq_answer is not None:
                yield f'[REPLY][咨询机器人]{faq_answer}'
                return
        setting = memory_context.set(getattr(task_agent, 'remembered_preferences', {}))
        try:
            async for token in task_agent.classify_task_stream(user_input):
                yield token
        finally:
            memory_context.reset(setting)
