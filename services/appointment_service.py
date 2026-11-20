"""
预约服务层

职责：
1. 封装预约相关的数据库操作
2. 处理预约业务逻辑
3. 提供预约相关的数据服务
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.db_router import DatabaseRouter
import logging

logger = logging.getLogger(__name__)

class AppointmentService:
    """预约服务类"""

    def __init__(self, db_path: str = 'sqlite:///data/smart_appointment.db'):
        self.db_router = DatabaseRouter(db_path)
        self.teacher_repo = self.db_router.teachers

    def save_appointment(self, teacher_id: str, start_time: datetime,
                        end_time: datetime, appointment_history: Dict[str, Any],
                        session_id: str) -> bool:
        """保存预约信息到数据库"""
        try:
            appointment_id = int(time.time() * 1000)

            # 保存预约到数据库
            self.teacher_repo.add_schedule(
                teacher_id=int(teacher_id),
                start_time=start_time,
                end_time=end_time,
                status="busy",
                appointment_id=appointment_id
            )

            logger.info(f"预约信息已保存到数据库：老师ID={teacher_id}, 时间={start_time} 到 {end_time}, 预约ID={appointment_id}")
            return True

        except Exception as e:
            logger.error(f"保存预约信息到数据库失败：{e}")
            return False

    def get_teacher_by_id(self, teacher_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取老师信息"""
        try:
            return self.teacher_repo.get_teacher_by_id(teacher_id)
        except Exception as e:
            logger.error(f"获取老师信息失败：{e}")
            return None

    def get_teacher_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据姓名获取老师信息"""
        try:
            return self.teacher_repo.get_teacher_by_name(name)
        except Exception as e:
            logger.error(f"获取老师信息失败：{e}")
            return None

    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """获取所有老师信息"""
        try:
            return self.teacher_repo.get_all_teachers()
        except Exception as e:
            logger.error(f"获取老师列表失败：{e}")
            return []

    def get_teachers_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        """根据性别获取老师信息"""
        try:
            return self.teacher_repo.get_teachers_by_gender(gender)
        except Exception as e:
            logger.error(f"根据性别获取老师信息失败：{e}")
            return []

    def get_teacher_schedules(self, teacher_id: int, date) -> List[Dict[str, Any]]:
        """获取老师排班信息"""
        try:
            return self.teacher_repo.get_teacher_schedules(teacher_id, date)
        except Exception as e:
            logger.error(f"获取老师排班信息失败：{e}")
            return []

    def is_teacher_available(self, teacher_id: int, start_time: datetime, end_time: datetime) -> bool:
        """检查老师是否可用"""
        try:
            return self.teacher_repo.is_teacher_available(teacher_id, start_time, end_time)
        except Exception as e:
            logger.error(f"检查老师可用性失败：{e}")
            return False

    def add_teacher(self, name: str, gender: str = None, strength: str = None) -> Optional[int]:
        """添加新老师"""
        try:
            return self.teacher_repo.add_teacher(name, gender, strength)
        except Exception as e:
            logger.error(f"添加老师失败：{e}")
            return None

    def get_all_strengths(self) -> List[str]:
        """获取所有老师的专长列表"""
        try:
            return self.teacher_repo.get_all_strengths()
        except Exception as e:
            logger.error(f"获取老师专长列表失败：{e}")
            return []
