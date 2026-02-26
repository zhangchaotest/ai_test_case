#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
需求分析 API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.services import requirement_service

# 创建路由器
router = APIRouter(prefix="", tags=["analysis"])

# 数据模型
class AnalysisRequest(BaseModel):
    project_id: int
    raw_req: str
    instruction: str = ""

class BreakdownUpdate(BaseModel):
    module_name: str
    feature_name: str
    description: str
    acceptance_criteria: str
    priority: str
    source_content: str = ""

class StatusUpdate(BaseModel):
    status: str


@router.post("/analyze/stream")
def analyze_requirement_stream(body: AnalysisRequest):
    """分析需求（流式响应）"""
    try:
        if not body.raw_req or not body.project_id:
            raise HTTPException(400, "需求内容和项目ID不能为空")
        return StreamingResponse(
            requirement_service.analyze_requirement(
                body.project_id, body.raw_req, body.instruction
            ),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"需求分析失败: {str(e)}")


@router.get("/requirement_breakdown")
def list_breakdowns(
        page: int = 1,
        size: int = 10,
        project_id: int = None,
        feature: str = None,
        status: str = None
):
    """获取需求拆解结果列表"""
    try:
        return requirement_service.get_breakdowns(page, size, project_id, feature, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求拆解结果失败: {str(e)}")


@router.put("/requirement_breakdown/{item_id}")
def update_breakdown(item_id: int, body: BreakdownUpdate):
    """更新需求拆解项"""
    try:
        # 使用 model_dump 替代 dict
        success = requirement_service.update_breakdown(item_id, body.model_dump())
        if success:
            return {"status": "success"}
        raise HTTPException(500, "更新失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新需求拆解项失败: {str(e)}")


@router.put("/requirement_breakdown/{item_id}/status")
def change_breakdown_status(item_id: int, body: StatusUpdate):
    """更新需求拆解状态"""
    try:
        if body.status not in ['Pass', 'Reject', 'Discard', 'Pending']:
            raise HTTPException(400, "无效的状态")

        success = requirement_service.update_breakdown_status(item_id, body.status)
        if success:
            return {"status": "success", "message": f"状态已更新为 {body.status}"}
        raise HTTPException(500, "状态更新失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")
