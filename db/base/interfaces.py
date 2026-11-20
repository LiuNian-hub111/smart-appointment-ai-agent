from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseTeacherRepository(ABC):
    """
    老师数据访问抽象接口

    定义老师相关的所有数据操作方法
    """

    @abstractmethod
    def add_teacher(self, name: str, gender: Optional[str] = None, strength: Optional[str] = None) -> int:
        """添加老师"""
        pass

    @abstractmethod
    def get_teacher_by_id(self, teacher_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取老师信息"""
        pass

    @abstractmethod
    def get_teacher_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据姓名获取老师信息"""
        pass

    @abstractmethod
    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """获取所有老师"""
        pass

    @abstractmethod
    def get_all_strengths(self) -> List[str]:
        """获取所有老师的专长"""
        pass

    @abstractmethod
    def update_teacher(self, teacher_id: int, **updates) -> bool:
        """更新老师信息"""
        pass

    @abstractmethod
    def delete_teacher(self, teacher_id: int) -> bool:
        """删除老师"""
        pass

    @abstractmethod
    def get_teachers_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        """根据性别获取老师"""
        pass


class BaseScheduleRepository(ABC):
    """
    排班数据访问抽象接口

    定义排班相关的所有数据操作方法
    """

    @abstractmethod
    def add_schedule(self, teacher_id: int, start_time: datetime, end_time: datetime,
                    status: str, appointment_id: Optional[int] = None) -> int:
        """添加排班"""
        pass

    @abstractmethod
    def get_teacher_schedules(self, teacher_id: int, date: datetime) -> List[Dict[str, Any]]:
        """获取老师指定日期的排班"""
        pass

    @abstractmethod
    def is_teacher_available(self, teacher_id: int, start_time: datetime, end_time: datetime) -> bool:
        """检查老师时间段是否可用"""
        pass

    @abstractmethod
    def update_schedule_status(self, schedule_id: int, status: str, appointment_id: Optional[int] = None) -> bool:
        """更新排班状态"""
        pass

    @abstractmethod
    def delete_schedule(self, schedule_id: int) -> bool:
        """删除排班"""
        pass


class BaseKnowledgeRepository(ABC):
    """
    知识库数据访问抽象接口

    定义知识库相关的所有数据操作方法
    """

    @abstractmethod
    def add_document(self, content: str, category: str, keywords: Optional[List[str]] = None,
                    embedding: Optional[List[float]] = None) -> int:
        """添加知识文档"""
        pass

    @abstractmethod
    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """获取指定文档"""
        pass

    @abstractmethod
    def get_all_documents(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """获取所有文档"""
        pass

    @abstractmethod
    def update_document(self, doc_id: int, content: Optional[str] = None, category: Optional[str] = None,
                       keywords: Optional[List[str]] = None, embedding: Optional[List[float]] = None) -> bool:
        """更新文档"""
        pass

    @abstractmethod
    def delete_document(self, doc_id: int, soft_delete: bool = True) -> bool:
        """删除文档（支持软删除）"""
        pass

    @abstractmethod
    def search_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类搜索文档"""
        pass

    @abstractmethod
    def search_documents_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """按关键词搜索文档"""
        pass

    @abstractmethod
    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        pass

    @abstractmethod
    def get_documents_count(self) -> int:
        """获取文档总数"""
        pass


class BaseUserBehaviorRepository(ABC):
    """
    用户行为数据访问抽象接口

    定义用户行为分析相关的所有数据操作方法
    """

    @abstractmethod
    def record_behavior(self, user_id: str, action_type: str, action_data: Optional[Dict[str, Any]] = None,
                       teacher_id: Optional[int] = None, session_id: Optional[str] = None) -> int:
        """记录用户行为"""
        pass

    @abstractmethod
    def get_user_behaviors(self, user_id: str, action_type: Optional[str] = None,
                          days_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取用户行为历史"""
        pass

    @abstractmethod
    def update_user_preference(self, user_id: str, preference_type: str, preference_value: str) -> bool:
        """更新用户偏好"""
        pass

    @abstractmethod
    def get_user_preferences(self, user_id: str, preference_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取用户偏好"""
        pass

    @abstractmethod
    def create_recommendation(self, user_id: str, recommendation_type: str, content: str,
                            teacher_id: Optional[int] = None) -> int:
        """创建推荐"""
        pass

    @abstractmethod
    def get_pending_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """获取待发送的推荐"""
        pass

    @abstractmethod
    def mark_recommendation_sent(self, recommendation_id: int) -> bool:
        """标记推荐为已发送"""
        pass

    @abstractmethod
    def get_user_statistics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """获取用户统计信息"""
        pass
