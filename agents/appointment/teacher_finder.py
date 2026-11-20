"""
老师查找器

负责根据用户需求查找合适的老师
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from services.text_embedding import find_best_match_indices


class TeacherFinder:
    """老师查找器"""

    def __init__(self):
        pass

    def parse_time_and_duration(self, start_time_str: str, duration_str: str) -> tuple:
        """解析预约时间和时长"""
        if not start_time_str or start_time_str == "未知":
            return None, None, None

        if not duration_str or duration_str == "未知":
            return None, None, None

        try:
            from config.time_config import time_config
            start_time = time_config.parse_datetime(start_time_str)
            if start_time is None:
                return None, None, None

            # 从字符串中提取数字作为时长（分钟）
            duration_min = int(''.join(filter(str.isdigit, str(duration_str))))
            if duration_min <= 0:
                return None, None, None

            end_time = start_time + timedelta(minutes=duration_min)
            return start_time, end_time, duration_min
        except Exception:
            return None, None, None

    def find_specific_teacher(self, teacher_name: str, start_time: datetime,
                               end_time: datetime, yield_func: Optional[Callable] = None) -> Optional[Dict]:
        """查找指定老师的可用性"""
        # 通过Services层访问数据库
        from services.appointment_service import AppointmentService
        appointment_service = AppointmentService()

        if yield_func:
            yield_func(f"[THOUGHT][预约机器人] 用户指定了老师：{teacher_name}，正在查询该老师信息...\n")

        specific_tech = appointment_service.get_teacher_by_name(teacher_name)
        if specific_tech:
            if yield_func:
                yield_func(f"[THOUGHT][预约机器人] 找到老师：{specific_tech['name']}，正在检查档期...\n")

            if appointment_service.is_teacher_available(specific_tech["id"], start_time, end_time):
                if yield_func:
                    yield_func(f"[THOUGHT][预约机器人] {teacher_name}老师在指定时间有空\n")
                return specific_tech
            else:
                if yield_func:
                    yield_func(f"[THOUGHT][预约机器人] {teacher_name}老师在指定时间不空闲\n")
                return None
        else:
            if yield_func:
                yield_func(f"[THOUGHT][预约机器人] 未找到名为'{teacher_name}'的老师\n")
            return None

    def find_similar_available_teacher(self, target_teacher: Dict[str, Any],
                                        start_time: datetime, end_time: datetime,
                                        yield_func: Optional[Callable] = None) -> Optional[Dict]:
        """根据目标老师的专长查找相似且可用的老师"""
        # 通过Services层访问数据库
        from services.appointment_service import AppointmentService
        appointment_service = AppointmentService()

        if yield_func:
            yield_func(f"[THOUGHT][预约机器人] 正在根据{target_teacher['name']}的专长查找相似老师...\n")

        # 获取所有老师
        all_techs = appointment_service.get_all_teachers()
        if not all_techs:
            return None

        # 排除目标老师本身
        other_techs = [tech for tech in all_techs if tech['id'] != target_teacher['id']]
        if not other_techs:
            return None

        # 获取目标老师的专长
        target_strength = target_teacher.get('strength', '')
        if not target_strength:
            return None

        # 使用文本嵌入找到最相似的老师
        strengths = [tech.get('strength', '') for tech in other_techs]
        indices = find_best_match_indices(target_strength, strengths)

        if yield_func:
            yield_func(f"[THOUGHT][预约机器人] 根据专长相似度排序，准备检查可用性...\n")

        # 按相似度顺序检查老师可用性
        for index in indices:
            similar_tech = other_techs[index]
            if appointment_service.is_teacher_available(similar_tech["id"], start_time, end_time):
                if yield_func:
                    yield_func(f"[THOUGHT][预约机器人] 找到相似且可用的老师：{similar_tech['name']}\n")
                return similar_tech

        if yield_func:
            yield_func(f"[THOUGHT][预约机器人] 没有找到相似且可用的老师\n")
        return None

    def filter_teachers_by_preference(self, all_techs: list, preference: str) -> list:
        """根据偏好筛选老师"""
        if not preference or preference == "无":
            return all_techs

        strengths = [tech.get("strength", "") for tech in all_techs]
        indices = find_best_match_indices(preference, strengths)
        return [all_techs[i] for i in indices]

    def filter_teachers_by_gender(self, all_techs: list, gender: str) -> list:
        """根据性别筛选老师"""
        if not gender or gender == "未知" or gender == "无":
            return all_techs

        # 标准化性别表示
        gender = gender.strip().lower()
        if gender in ["男", "男性", "男老师", "male"]:
            target_gender = "男"
        elif gender in ["女", "女性", "女老师", "female"]:
            target_gender = "女"
        else:
            return all_techs

        # 筛选匹配性别的老师
        filtered_techs = []
        for tech in all_techs:
            tech_gender = tech.get("gender", "").strip()
            if tech_gender == target_gender:
                filtered_techs.append(tech)

        return filtered_techs if filtered_techs else all_techs  # 如果没有匹配的，返回所有老师

    def find_available_teacher(self, filtered_techs: list, all_techs: list,
                                start_time: datetime, end_time: datetime,
                                preference: str, gender: str = None, yield_func: Optional[Callable] = None) -> Optional[Dict]:
        """在老师列表中查找可用老师"""
        # 通过Services层访问数据库
        from services.appointment_service import AppointmentService
        appointment_service = AppointmentService()

        if yield_func:
            yield_func("[THOUGHT][预约机器人] 正在查找空闲老师...\n")

        # 先在筛选后的老师中查找
        for tech in filtered_techs:
            if appointment_service.is_teacher_available(tech["id"], start_time, end_time):
                if yield_func:
                    yield_func(f"[THOUGHT][预约机器人] 找到空闲老师：{tech['name']}\n")
                return tech

        # 如果有偏好但没找到，再在所有老师中查找
        if preference and preference != "无" and filtered_techs != all_techs:
            if yield_func:
                yield_func("[THOUGHT][预约机器人] 偏好老师无空闲，尝试查找所有老师...\n")
            for tech in all_techs:
                if appointment_service.is_teacher_available(tech["id"], start_time, end_time):
                    if yield_func:
                        yield_func(f"[THOUGHT][预约机器人] 找到空闲老师：{tech['name']}\n")
                    return tech

        if yield_func:
            yield_func("[THOUGHT][预约机器人] 没有找到空闲老师\n")
        return None

    def find_teacher_with_thought(self, appointment_history: Dict[str, Any],
                                   yield_func: Optional[Callable] = None) -> Optional[Dict]:
        """带思考提示的老师检索流程"""
        # 通过Services层访问数据库
        from services.appointment_service import AppointmentService
        appointment_service = AppointmentService()

        preference = appointment_history.get("preference")
        start_time_str = appointment_history.get("start_time")
        duration_str = appointment_history.get("duration")
        teacher_name = appointment_history.get("teacher_name")

        # 解析时间和时长
        start_time, end_time, duration_min = self.parse_time_and_duration(start_time_str, duration_str)
        if not start_time or not end_time:
            if yield_func:
                yield_func("[THOUGHT][预约机器人] 预约时间或时长信息不完整，无法检索老师\n")
            return None

        if yield_func:
            yield_func("[THOUGHT][预约机器人] 正在解析预约时间和时长...\n")

        # 优先处理指定老师
        if teacher_name and teacher_name != "未知":
            specific_tech = self.find_specific_teacher(teacher_name, start_time, end_time, yield_func)

            # 如果指定老师可用，直接返回
            if specific_tech:
                return specific_tech

            # 如果指定老师不可用，查找相似老师并返回推荐信息
            target_tech = appointment_service.get_teacher_by_name(teacher_name)
            if target_tech:
                similar_tech = self.find_similar_available_teacher(target_tech, start_time, end_time, yield_func)
                if similar_tech:
                    # 返回包含推荐信息的结果，但标记为需要用户确认
                    return {
                        'is_recommendation': True,
                        'original_teacher': target_tech,
                        'recommended_teacher': similar_tech,
                        'requires_confirmation': True
                    }

            # 如果没有找到目标老师或相似老师，返回None
            return None

        # 通用查询逻辑
        if yield_func:
            yield_func("[THOUGHT][预约机器人] 正在检索所有老师数据...\n")

        all_techs = appointment_service.get_all_teachers()
        if not all_techs:
            if yield_func:
                yield_func("[THOUGHT][预约机器人] 没有找到任何老师数据\n")
            return None

        # 课程主题是必需条件，用老师的教学专长匹配
        course = appointment_history.get("project", "")
        filtered_techs = self.filter_teachers_by_preference(all_techs, course)
        if preference and preference not in ("无", "未知"):
            filtered_techs = self.filter_teachers_by_preference(filtered_techs, preference)
        if yield_func and preference and preference != "无":
            yield_func(f"[THOUGHT][预约机器人] 根据课程和偏好筛选，找到{len(filtered_techs)}位老师\n")

        # 仅在匹配课程的老师中查询档期
        return self.find_available_teacher(filtered_techs, filtered_techs, start_time, end_time, preference, None, yield_func)
