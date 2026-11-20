# utils/ai/teacher_service.py

from typing import List, Dict, Any
from db.db_router import DatabaseRouter
import logging

logger = logging.getLogger(__name__)

class TeacherService:
    """老师数据服务；沿用原项目的内部类名和数据库表名。"""

    def __init__(self):
        self.db = DatabaseRouter()

        # 仅供本地演示；正式使用时应换成真实老师和课程资料
        self.default_teachers = [
            {"name": "演示老师A", "gender": None, "strength": "高中物理力学、运动学、牛顿定律"},
            {"name": "演示老师B", "gender": None, "strength": "高中物理电磁学、电路、磁场"},
            {"name": "演示老师C", "gender": None, "strength": "高中物理力学、能量守恒、动量"},
        ]

    def initialize_default_teachers(self) -> bool:
        """初始化默认老师数据"""
        try:
            # 检查是否已有老师数据
            existing_teachers = self.db.teachers.get_all_teachers()

            if existing_teachers:
                logger.info(f"数据库中已有 {len(existing_teachers)} 位老师，跳过初始化")
                return True

            logger.info("数据库中无老师数据，开始初始化默认老师")

            # 添加默认老师
            for tech_data in self.default_teachers:
                try:
                    tech_id = self.db.teachers.add_teacher(
                        name=tech_data['name'],
                        gender=tech_data['gender'],
                        strength=tech_data['strength']
                    )
                    logger.debug(f"添加老师: {tech_data['name']} (ID: {tech_id})")

                except Exception as e:
                    logger.error(f"添加老师 {tech_data['name']} 失败: {e}")
                    return False

            # 验证初始化结果
            final_count = len(self.db.teachers.get_all_teachers())
            logger.info(f"老师初始化完成，共添加 {final_count} 位老师")
            return True

        except Exception as e:
            logger.error(f"老师初始化失败: {e}")
            return False

    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """获取所有老师信息"""
        return self.db.teachers.get_all_teachers()

    def get_teacher_by_name(self, name: str) -> Dict[str, Any]:
        """根据姓名获取老师信息"""
        return self.db.teachers.get_teacher_by_name(name)

    def get_teacher_by_id(self, teacher_id: int) -> Dict[str, Any]:
        """根据ID获取老师信息"""
        return self.db.teachers.get_teacher_by_id(teacher_id)

    def get_teacher_schedules(self, teacher_id: int, date) -> List[Dict[str, Any]]:
        """获取老师指定日期的排班信息"""
        return self.db.teachers.get_teacher_schedules(teacher_id, date)

    def is_teacher_available(self, teacher_id: int, start_time, end_time) -> bool:
        """检查老师在指定时间段是否可用"""
        return self.db.teachers.is_teacher_available(teacher_id, start_time, end_time)

    def add_teacher(self, name: str, gender: str = None, strength: str = None) -> int:
        """添加新老师"""
        return self.db.teachers.add_teacher(name, gender, strength)

    def get_teachers_count(self) -> int:
        """获取老师总数"""
        teachers = self.db.teachers.get_all_teachers()
        return len(teachers)

    def get_teacher_by_id(self, teacher_id: int) -> Dict[str, Any]:
        """根据ID获取老师信息"""
        return self.db.teachers.get_teacher_by_id(teacher_id)

    def get_teacher_schedules(self, teacher_id: int, date) -> List[Dict[str, Any]]:
        """获取老师指定日期的排班信息"""
        return self.db.teachers.get_teacher_schedules(teacher_id, date)

    def is_teacher_available(self, teacher_id: int, start_time, end_time) -> bool:
        """检查老师在指定时间段是否可用"""
        return self.db.teachers.is_teacher_available(teacher_id, start_time, end_time)
