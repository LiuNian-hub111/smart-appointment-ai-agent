"""
提示词构建器

负责构建各种类型的提示词
"""

from typing import List, Dict, Any


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
        self.classification_prompt_template = self._create_classification_prompt_template()
    
    def _create_system_prompt(self) -> str:
        """创建系统提示词"""
        return (
            "你是物理辅导约课助手，回答学生关于课程内容、价格、流程和老师课表的问题。"
            "只根据提供的知识库信息回答具体事实。价格、上课地点、老师资质、取消规则没有明确资料时，直接说明尚未确认，请向老师核实。"
            "不要编造金额、时间或地址。表达要礼貌、简洁。"
            "与物理辅导无关的问题，说明当前只处理课程咨询和约课。"
        )
    
    def _create_classification_prompt_template(self) -> str:
        """创建分类提示词模板"""
        return (
            "你是一个分类器，判断学生输入是否是物理辅导课程的咨询问题。\n"
            "咨询类问题包括：课程内容、价格、老师、上课方式、约课流程等。\n"
            "非咨询类问题包括：直接请求约课、取消约课，以及天气、股票等无关话题。\n"
            "如果是咨询类问题，回答'YES'。如果是预约类问题或完全无关问题，回答'NO'。\n"
            "只回答YES或NO。\n\n"
            "用户输入：{user_input}"
        )
    
    def build_consultation_prompt(self, user_input: str, knowledge_docs: List[Dict[str, Any]]) -> str:
        """构建咨询提示词"""
        context = self._build_knowledge_context(knowledge_docs)
        return f"{self.system_prompt}\n\n{context}\n用户问题：{user_input}\n\n请回答用户的问题。"
    
    def build_classification_prompt(self, user_input: str) -> str:
        """构建分类提示词"""
        return self.classification_prompt_template.format(user_input=user_input)
    
    def _build_knowledge_context(self, knowledge_docs: List[Dict[str, Any]]) -> str:
        """构建知识库上下文"""
        if not knowledge_docs:
            return "没有找到相关课程资料。具体价格、时间和规则请向老师确认，不要猜测。"
        
        context = "\n以下是相关的知识库信息：\n"
        for i, doc in enumerate(knowledge_docs, 1):
            context += f"{i}. {doc['content']}\n"
        context += "\n请只依据以上资料回答具体事实；资料不足时明确说尚未确认。\n"
        
        return context
