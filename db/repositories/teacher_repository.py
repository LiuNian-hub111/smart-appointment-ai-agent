from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from ..base.interfaces import BaseTeacherRepository, BaseScheduleRepository
from ..base.session_manager import SessionManager
from ..models import Teacher, TeacherSchedule


class TeacherRepository(BaseTeacherRepository, BaseScheduleRepository):
    """
    老师数据访问对象

    职责：
    1. 老师信息的CRUD操作
    2. 老师排班的管理
    3. 老师可用性检查
    """

    def __init__(self, session_manager: SessionManager):
        """
        初始化老师数据仓库

        Args:
            session_manager: 会话管理器
        """
        self.session_manager = session_manager

    def add_teacher(self, name: str, gender: Optional[str] = None, strength: Optional[str] = None) -> int:
        """
        添加新老师

        Args:
            name: 老师姓名
            gender: 性别
            strength: 专长

        Returns:
            新创建的老师ID
        """
        with self.session_manager.session_scope() as session:
            teacher = Teacher(name=name, gender=gender, strength=strength)
            session.add(teacher)
            session.flush()
            return teacher.id

    def get_teacher_by_id(self, teacher_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取老师信息

        Args:
            teacher_id: 老师ID

        Returns:
            老师信息字典，如果不存在返回None
        """
        with self.session_manager.session_scope() as session:
            teacher = session.query(Teacher).filter(
                Teacher.id == teacher_id
            ).first()

            if not teacher:
                return None

            return self._teacher_to_dict(teacher)

    def get_teacher_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据姓名获取老师信息

        Args:
            name: 老师姓名

        Returns:
            老师信息字典，如果不存在返回None
        """
        with self.session_manager.session_scope() as session:
            teacher = session.query(Teacher).filter(
                Teacher.name == name
            ).first()

            if not teacher:
                return None

            return self._teacher_to_dict(teacher)

    def get_all_teachers(self) -> List[Dict[str, Any]]:
        """
        获取所有老师信息

        Returns:
            老师信息列表
        """
        with self.session_manager.session_scope() as session:
            teachers = session.query(Teacher).all()
            return [self._teacher_to_dict(tech) for tech in teachers]

    def get_all_strengths(self) -> List[str]:
        """
        获取所有老师的专长列表

        Returns:
            专长列表（去重后）
        """
        with self.session_manager.session_scope() as session:
            strengths = session.query(Teacher.strength).distinct().all()
            return [s[0] for s in strengths if s[0] is not None]

    def update_teacher(self, teacher_id: int, **updates) -> bool:
        """
        更新老师信息

        Args:
            teacher_id: 老师ID
            **updates: 要更新的字段

        Returns:
            更新是否成功
        """
        with self.session_manager.session_scope() as session:
            teacher = session.query(Teacher).filter(
                Teacher.id == teacher_id
            ).first()

            if not teacher:
                return False

            for key, value in updates.items():
                if hasattr(teacher, key):
                    setattr(teacher, key, value)

            return True

    def delete_teacher(self, teacher_id: int) -> bool:
        """
        删除老师

        Args:
            teacher_id: 老师ID

        Returns:
            删除是否成功
        """
        with self.session_manager.session_scope() as session:
            teacher = session.query(Teacher).filter(
                Teacher.id == teacher_id
            ).first()

            if not teacher:
                return False

            session.delete(teacher)
            return True

    # 排班相关方法
    def add_schedule(self, teacher_id: int, start_time: datetime, end_time: datetime,
                    status: str, appointment_id: Optional[int] = None) -> int:
        """
        添加老师排班

        Args:
            teacher_id: 老师ID
            start_time: 开始时间
            end_time: 结束时间
            status: 状态 ('busy' 或 'free')
            appointment_id: 预约ID（如果是忙碌状态）

        Returns:
            新创建的排班ID
        """
        if start_time >= end_time:
            raise ValueError("约课结束时间必须晚于开始时间")
        with self.session_manager.session_scope() as session:
            if status == "busy":
                # SQLite's deferred transaction would let two writers both pass
                # the conflict query. Reserve the write lock before querying.
                if session.bind.dialect.name == "sqlite":
                    session.execute(text("BEGIN IMMEDIATE"))
                conflict = session.query(TeacherSchedule).filter(
                    TeacherSchedule.teacher_id == teacher_id,
                    TeacherSchedule.status == "busy",
                    TeacherSchedule.start_time < end_time,
                    TeacherSchedule.end_time > start_time,
                ).first()
                if conflict is not None:
                    raise ValueError("老师在该时间段已有课程")
            schedule = TeacherSchedule(
                teacher_id=teacher_id,
                start_time=start_time,
                end_time=end_time,
                status=status,
                appointment_id=appointment_id
            )
            session.add(schedule)
            session.flush()
            return schedule.id

    def get_teacher_schedules(self, teacher_id: int, date: datetime) -> List[Dict[str, Any]]:
        """
        获取老师指定日期的排班

        Args:
            teacher_id: 老师ID
            date: 查询日期

        Returns:
            排班信息列表
        """
        with self.session_manager.session_scope() as session:
            start = datetime(date.year, date.month, date.day)
            end = start + timedelta(days=1)

            schedules = session.query(TeacherSchedule).filter(
                TeacherSchedule.teacher_id == teacher_id,
                TeacherSchedule.start_time >= start,
                TeacherSchedule.end_time < end
            ).all()

            return [self._schedule_to_dict(schedule) for schedule in schedules]

    def is_teacher_available(self, teacher_id: int, start_time: datetime, end_time: datetime) -> bool:
        """
        检查老师在指定时间段是否可用

        Args:
            teacher_id: 老师ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            是否可用
        """
        with self.session_manager.session_scope() as session:
            conflict = session.query(TeacherSchedule).filter(
                TeacherSchedule.teacher_id == teacher_id,
                TeacherSchedule.status == "busy",
                TeacherSchedule.start_time < end_time,
                TeacherSchedule.end_time > start_time
            ).first()

            return conflict is None

    def update_schedule_status(self, schedule_id: int, status: str, appointment_id: Optional[int] = None) -> bool:
        """
        更新排班状态

        Args:
            schedule_id: 排班ID
            status: 新状态
            appointment_id: 预约ID

        Returns:
            更新是否成功
        """
        with self.session_manager.session_scope() as session:
            schedule = session.query(TeacherSchedule).filter(
                TeacherSchedule.id == schedule_id
            ).first()

            if not schedule:
                return False

            schedule.status = status
            if appointment_id is not None:
                schedule.appointment_id = appointment_id

            return True

    def delete_schedule(self, schedule_id: int) -> bool:
        """
        删除排班

        Args:
            schedule_id: 排班ID

        Returns:
            删除是否成功
        """
        with self.session_manager.session_scope() as session:
            schedule = session.query(TeacherSchedule).filter(
                TeacherSchedule.id == schedule_id
            ).first()

            if not schedule:
                return False

            session.delete(schedule)
            return True

    def get_teachers_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        """
        根据性别获取老师信息

        Args:
            gender: 老师性别

        Returns:
            老师信息列表
        """
        with self.session_manager.session_scope() as session:
            teachers = session.query(Teacher).filter(
                Teacher.gender == gender
            ).all()
            return [self._teacher_to_dict(tech) for tech in teachers]

    def _teacher_to_dict(self, teacher: Teacher) -> Dict[str, Any]:
        """将老师对象转换为字典"""
        return {
            'id': teacher.id,
            'name': teacher.name,
            'gender': teacher.gender,
            'strength': teacher.strength
        }

    def _schedule_to_dict(self, schedule: TeacherSchedule) -> Dict[str, Any]:
        """将排班对象转换为字典"""
        return {
            'id': schedule.id,
            'teacher_id': schedule.teacher_id,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'status': schedule.status,
            'appointment_id': schedule.appointment_id
        }
