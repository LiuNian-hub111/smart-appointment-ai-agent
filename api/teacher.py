"""
老师信息与排班查询 API

提供老师信息和排班查询接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/teachers", tags=["老师管理"])


class TeacherResponse(BaseModel):
    """老师信息响应"""
    id: int
    name: str
    gender: str | None = None
    strength: str


class ScheduleResponse(BaseModel):
    """排班信息响应"""
    id: int
    teacher_id: int
    start_time: str
    end_time: str
    status: str
    appointment_id: int | None = None


@router.get("/", response_model=List[TeacherResponse], summary="获取所有老师")
async def get_all_teachers():
    """获取所有老师信息"""
    try:
        from services.teacher_service import TeacherService
        teacher_service = TeacherService()
        teacher_service.initialize_default_teachers()
        teachers = teacher_service.get_all_teachers()
        
        return [
            TeacherResponse(
                id=tech["id"],
                name=tech["name"],
                gender=tech.get("gender", ""),
                strength=tech.get("strength", "")
            )
            for tech in teachers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取老师信息失败: {str(e)}")


@router.get("/{teacher_id}/schedule", response_model=List[ScheduleResponse], summary="获取老师排班")
async def get_teacher_schedule(teacher_id: int):
    """获取指定老师今天的排班信息"""
    try:
        from services.teacher_service import TeacherService
        from config.time_config import time_config
        
        teacher_service = TeacherService()
        teacher_service.initialize_default_teachers()
        
        # 获取老师信息确认存在
        tech = teacher_service.get_teacher_by_id(teacher_id)
        if not tech:
            raise HTTPException(status_code=404, detail="老师不存在")
        
        # 获取今天的排班
        today = time_config.today()
        schedules = teacher_service.get_teacher_schedules(teacher_id, today)
        
        return [
            ScheduleResponse(
                id=sched["id"],
                teacher_id=sched["teacher_id"],
                start_time=sched["start_time"].strftime("%H:%M"),
                end_time=sched["end_time"].strftime("%H:%M"),
                status=sched["status"],
                appointment_id=sched.get("appointment_id")
            )
            for sched in schedules
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排班信息失败: {str(e)}")


@router.get("/{teacher_id}", response_model=TeacherResponse, summary="获取单个老师信息")
async def get_teacher(teacher_id: int):
    """获取指定老师的详细信息"""
    try:
        from services.teacher_service import TeacherService
        
        teacher_service = TeacherService()
        teacher_service.initialize_default_teachers()
        tech = teacher_service.get_teacher_by_id(teacher_id)
        
        if not tech:
            raise HTTPException(status_code=404, detail="老师不存在")
        
        return TeacherResponse(
            id=tech["id"],
            name=tech["name"],
            gender=tech.get("gender", ""),
            strength=tech.get("strength", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取老师信息失败: {str(e)}")


@router.get("/schedules/today", summary="获取所有老师今日排班")
async def get_all_teachers_schedule_today():
    """获取所有老师今天的排班信息"""
    try:
        from services.teacher_service import TeacherService
        from config.time_config import time_config
        
        teacher_service = TeacherService()
        teacher_service.initialize_default_teachers()
        
        # 获取所有老师
        all_teachers = teacher_service.get_all_teachers()
        today = time_config.today()
        
        schedules_data = []
        for tech in all_teachers:
            tech_id = tech["id"]
            tech_name = tech["name"]
            
            # 获取该老师今天的排班
            tech_schedules = teacher_service.get_teacher_schedules(tech_id, today)
            
            busy_periods = []
            for sched in tech_schedules:
                if sched.get("status") == "busy":
                    busy_periods.append({
                        "start": sched["start_time"].strftime("%H:%M") if hasattr(sched["start_time"], 'strftime') else str(sched["start_time"]),
                        "end": sched["end_time"].strftime("%H:%M") if hasattr(sched["end_time"], 'strftime') else str(sched["end_time"]),
                        "appointment_id": sched.get("appointment_id")
                    })
            
            schedules_data.append({
                "teacher_id": tech_id,
                "teacher_name": tech_name,
                "busy_periods": busy_periods
            })
        
        return schedules_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排班信息失败: {str(e)}")
