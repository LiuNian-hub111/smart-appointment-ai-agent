# utils/ai/technician_service.py

from typing import List, Dict, Any
from db.db_router import DatabaseRouter
import logging

logger = logging.getLogger(__name__)

class TechnicianService:
    """老师数据服务；沿用原项目的内部类名和数据库表名。"""
    
    def __init__(self):
        self.db = DatabaseRouter()
        
        # 仅供本地演示；正式使用时应换成真实老师和课程资料
        self.default_technicians = [
            {"name": "演示老师A", "gender": None, "strength": "高中物理力学、运动学、牛顿定律"},
            {"name": "演示老师B", "gender": None, "strength": "高中物理电磁学、电路、磁场"},
            {"name": "演示老师C", "gender": None, "strength": "高中物理力学、能量守恒、动量"},
        ]

    def initialize_default_technicians(self) -> bool:
        """初始化默认技师数据"""
        try:
            # 检查是否已有技师数据
            existing_technicians = self.db.technicians.get_all_technicians()
            
            if existing_technicians:
                logger.info(f"数据库中已有 {len(existing_technicians)} 位技师，跳过初始化")
                return True
            
            logger.info("数据库中无技师数据，开始初始化默认技师")
            
            # 添加默认技师
            for tech_data in self.default_technicians:
                try:
                    tech_id = self.db.technicians.add_technician(
                        name=tech_data['name'],
                        gender=tech_data['gender'],
                        strength=tech_data['strength']
                    )
                    logger.debug(f"添加技师: {tech_data['name']} (ID: {tech_id})")
                    
                except Exception as e:
                    logger.error(f"添加技师 {tech_data['name']} 失败: {e}")
                    return False
            
            # 验证初始化结果
            final_count = len(self.db.technicians.get_all_technicians())
            logger.info(f"技师初始化完成，共添加 {final_count} 位技师")
            return True
            
        except Exception as e:
            logger.error(f"技师初始化失败: {e}")
            return False

    def get_all_technicians(self) -> List[Dict[str, Any]]:
        """获取所有技师信息"""
        return self.db.technicians.get_all_technicians()

    def get_technician_by_name(self, name: str) -> Dict[str, Any]:
        """根据姓名获取技师信息"""
        return self.db.technicians.get_technician_by_name(name)

    def get_technician_by_id(self, technician_id: int) -> Dict[str, Any]:
        """根据ID获取技师信息"""
        return self.db.technicians.get_technician_by_id(technician_id)

    def get_technician_schedules(self, technician_id: int, date) -> List[Dict[str, Any]]:
        """获取技师指定日期的排班信息"""
        return self.db.technicians.get_technician_schedules(technician_id, date)

    def is_technician_available(self, technician_id: int, start_time, end_time) -> bool:
        """检查技师在指定时间段是否可用"""
        return self.db.technicians.is_technician_available(technician_id, start_time, end_time)

    def add_technician(self, name: str, gender: str = None, strength: str = None) -> int:
        """添加新技师"""
        return self.db.technicians.add_technician(name, gender, strength)

    def get_technicians_count(self) -> int:
        """获取技师总数"""
        technicians = self.db.technicians.get_all_technicians()
        return len(technicians)

    def get_technician_by_id(self, technician_id: int) -> Dict[str, Any]:
        """根据ID获取技师信息"""
        return self.db.technicians.get_technician_by_id(technician_id)

    def get_technician_schedules(self, technician_id: int, date) -> List[Dict[str, Any]]:
        """获取技师指定日期的排班信息"""
        return self.db.technicians.get_technician_schedules(technician_id, date)

    def is_technician_available(self, technician_id: int, start_time, end_time) -> bool:
        """检查技师在指定时间段是否可用"""
        return self.db.technicians.is_technician_available(technician_id, start_time, end_time)
