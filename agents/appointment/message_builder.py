"""
消息构建器

负责构建各种响应消息
"""

from typing import Dict, Any, List


class MessageBuilder:
    """消息构建器"""
    
    def __init__(self):
        self.missing_info_prompts = {
            "start_time": "请问您想什么时候上课？",
            "duration": "请问您想上多长时间的课？",
            "project": "请问您想学习哪部分物理内容？例如高中力学。",
            "preference": "您对老师的教学方向有什么偏好吗？"
        }
    
    def create_appointment_success_message(self, tech: Dict[str, Any]) -> str:
        """创建预约成功消息"""
        # 检查是否是推荐技师
        if tech.get('is_recommendation'):
            original_tech = tech.get('original_technician', {})
            return (f"\n机器人：已为您预约物理老师：{tech['name']}。约课成功！"
                    f"（原指定的{original_tech.get('name', '')}老师时间冲突，已按您的确认改约。）\n")
        else:
            return f"\n机器人：已为您预约物理老师：{tech['name']}。约课成功！\n"

    def create_technician_recommendation_message(self, original_tech: Dict[str, Any], 
                                               recommended_tech: Dict[str, Any], 
                                               appointment_history: Dict[str, Any],
                                               llm=None) -> str:
        """创建技师推荐消息，使用LLM生成个性化措辞"""
        project = appointment_history.get('project', '物理辅导')
        start_time = appointment_history.get('start_time', '')
        
        if llm:
            try:
                # 构建LLM提示
                prompt = f"""
作为物理辅导约课助手，学生想预约{original_tech['name']}老师学习{project}，但该老师在{start_time}没有空档。

我找到了一位教学方向相近的老师：
- 姓名：{recommended_tech['name']}
- 教学专长：{recommended_tech.get('strength', '')}

原老师教学专长：{original_tech.get('strength', '')}

请告诉学生原老师没空，推荐老师的教学方向相近且该时段有空，并明确询问学生是否同意改约。不要声称两位老师教学效果相同。

要求：
1. 语气温和、专业
2. 说明推荐老师的教学方向
3. 明确询问用户意愿
4. 字数控制在80字以内
"""
                
                response = llm.invoke(prompt)
                if hasattr(response, 'content'):
                    generated_msg = response.content.strip()
                    if generated_msg:
                        return f"\n机器人：{generated_msg}\n"
                
            except Exception as e:
                print(f"LLM生成推荐消息失败: {e}")
        
        # 如果LLM失败，使用默认消息
        return (f"\n机器人：抱歉，{original_tech['name']}老师在{start_time}没有空档。"
                f"{recommended_tech['name']}老师的教学方向与{project}相关，且该时间有空。"
                f"您愿意改约{recommended_tech['name']}老师吗？\n")

    def create_recommendation_declined_message(self, llm=None) -> str:
        """创建用户拒绝推荐时的消息"""
        if llm:
            try:
                prompt = """
学生拒绝了我推荐的老师，请简短回复，并提供更换时间或老师的选择。

要求：
1. 表达理解用户的选择
2. 提供其他解决方案（如换时间、重新选择等）
3. 保持专业和友好的语气
4. 字数控制在60字以内
"""
                response = llm.invoke(prompt)
                if hasattr(response, 'content'):
                    generated_msg = response.content.strip()
                    if generated_msg:
                        return f"\n机器人：{generated_msg}\n"
            except Exception as e:
                print(f"LLM生成拒绝消息失败: {e}")
        
        # 默认消息
        return "\n机器人：好的。您可以更换上课时间，或让我推荐其他物理老师。\n"
    
    def create_appointment_failure_message(self, technician_name: str) -> str:
        """创建预约失败消息"""
        if technician_name and technician_name != "未知":
            # 通过Services层访问数据库
            from services.appointment_service import AppointmentService
            appointment_service = AppointmentService()
            specific_tech = appointment_service.get_technician_by_name(technician_name)
            if specific_tech:
                return f"\n机器人：抱歉，{technician_name}老师在您选择的时间段不空闲。请选择其他时间，或者我可以推荐其他老师。\n"
            else:
                return f"\n机器人：抱歉，没有找到名为'{technician_name}'的老师。请确认姓名，或者让我推荐其他老师。\n"
        else:
            return "\n机器人：抱歉，该时间段没有合适的物理老师空闲，请选择其他时间或调整课程需求。\n"
    
    def create_missing_info_questions(self, missing_info: List[str]) -> str:
        """根据缺失信息创建询问"""
        questions = [self.missing_info_prompts.get(field, f"请补充{field}信息") for field in missing_info]
        return "\n" + " ".join(questions) + "\n"
    
    def create_unrelated_message(self) -> str:
        """创建无关请求的消息"""
        return "[REPLY][预约机器人]抱歉，我只能帮您咨询物理辅导和约课。您想了解课程还是预约上课？\n"
    
    def create_parse_error_message(self) -> str:
        """创建解析错误消息"""
        return "[REPLY][预约机器人]\n机器人：解析失败，请重试。\n"
    
    def create_save_failure_message(self) -> str:
        """创建保存失败消息"""
        return "\n机器人：抱歉，预约保存失败，请重试。\n"
