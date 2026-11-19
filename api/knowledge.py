"""
知识库管理API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


class KnowledgeItem(BaseModel):
    id: int = None
    question: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)
    content: str | None = Field(default=None, min_length=1)
    category: str = "general"
    keywords: List[str] | None = None

    @field_validator("question", "answer", "content")
    @classmethod
    def reject_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:raise ValueError("不能为空")
        return value

    @model_validator(mode="after")
    def require_content_or_question_and_answer(self):
        if self.content is not None:
            if self.question is not None or self.answer is not None:
                raise ValueError("知识内容与问答只能选择一种")
        elif self.question is None or self.answer is None:
            raise ValueError("请提供知识内容或完整问答")
        return self

    def document_content(self) -> str:
        if self.content is not None:
            return self.content
        return f"问题: {self.question}\n答案: {self.answer}"


class SearchRequest(BaseModel):
    query: str


@router.get("/")
async def get_all_knowledge():
    """获取所有知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        entries = knowledge_service.get_all_documents()
        
        # 安全获取categories，避免出错
        try:
            categories = knowledge_service.get_all_categories()
        except Exception as e:
            print(f"获取categories失败: {e}")
            categories = []
        
        return {
            "documents": entries or [],
            "categories": categories or [],
            "total_count": len(entries) if entries else 0,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库失败: {str(e)}")


@router.get("/{knowledge_id}")
async def get_knowledge(knowledge_id: int):
    """获取特定知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        entry = knowledge_service.get_document(knowledge_id)
        if not entry:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {
            "status": "success",
            "data": entry
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识条目失败: {str(e)}")


@router.post("/")
async def add_knowledge(item: KnowledgeItem):
    """添加新的知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        document = {"content": item.document_content(), "category": item.category}
        if item.keywords is not None:
            document["keywords"] = item.keywords
        result = await knowledge_service.add_document(**document)
        if not result:
            raise HTTPException(status_code=500, detail="知识条目保存失败")
        return {
            "status": "success",
            "message": "知识条目添加成功",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加知识条目失败: {str(e)}")


@router.put("/{knowledge_id}")
async def update_knowledge(knowledge_id: int, item: KnowledgeItem):
    """更新知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        document = {"content": item.document_content(), "category": item.category}
        if item.keywords is not None:
            document["keywords"] = item.keywords
        result = await knowledge_service.update_document(doc_id=knowledge_id, **document)
        if not result:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {
            "status": "success",
            "message": "知识条目更新成功",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新知识条目失败: {str(e)}")


@router.delete("/{knowledge_id}")
async def delete_knowledge(knowledge_id: int):
    """删除知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        result = await knowledge_service.delete_document(knowledge_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {
            "status": "success",
            "message": "知识条目删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除知识条目失败: {str(e)}")


@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """搜索知识库"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        results = await knowledge_service.search(request.query)
        return {
            "status": "success",
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索知识库失败: {str(e)}")
