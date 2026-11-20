from agents.task_classification_agent import TaskClassificationAgent
from agents.appointment_agent import AppointmentAgent
from agents.consultant_agent import ConsultantAgent
from services.common_faq import answer_common_question
import uuid

# 全局session_id用于单用户场景
global_session_id = str(uuid.uuid4())

task_agent = TaskClassificationAgent(
    AppointmentAgent(session_id=global_session_id), 
    ConsultantAgent(session_id=global_session_id)
)

async def ProcessUserInput_stream(user_input, state=None, context=None):
    """
    user_input: 用户输入
    state: 当前对话状态（如 None, 'classify', 'appointment', 'query', ...）
    context: 可选，保存多轮对话上下文（如 dict，可存储 agent 的 history 等）
    返回: (reply, next_state, next_context)
    """
    # 初始化 context
    if context is None:
        context = {}

    # Fixed price and booking-process facts can be read directly from the
    # knowledge base, avoiding slow or rate-limited model calls.
    if task_agent.state_manager.should_classify():
        faq_answer = answer_common_question(user_input)
        if faq_answer is not None:
            yield f"[REPLY][咨询机器人]{faq_answer}"
            return

    async for token in task_agent.classify_task_stream(user_input):
        yield token
