"""Business services, loaded on demand so booking does not initialize embeddings."""

from importlib import import_module

_EXPORTS = {
    'embed_input': 'text_embedding',
    'find_best_match_indices': 'text_embedding',
    'save_teacher_embeddings': 'text_embedding',
    'load_teacher_embeddings': 'text_embedding',
    'KnowledgeService': 'knowledge_service',
    'TeacherService': 'teacher_service',
    'AppointmentService': 'appointment_service',
    'UserBehaviorService': 'user_behavior_service',
    'RecommendationService': 'recommendation_service',
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(f'.{_EXPORTS[name]}', __name__), name)
    globals()[name] = value
    return value
