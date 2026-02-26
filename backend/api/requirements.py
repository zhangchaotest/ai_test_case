#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试需求管理和测试用例生成 API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List

from backend.services import requirement_service, test_case_service

# 创建路由器
router = APIRouter(prefix="", tags=["requirements"])

# 数据模型
class BatchGenerateRequest(BaseModel):
    ids: List[int]
    count: int = 5


@router.get("")
def list_requirements(page: int = 1, size: int = 10, feature: str = None):
    """获取功能点列表"""
    try:
        return requirement_service.get_requirements(page, size, feature_name=feature)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能点列表失败: {str(e)}")


@router.get("/{req_id}/generate_stream")
async def generate_cases_stream(req_id: int, count: int = 5, mode: str = "new", domain: str = "base", prompt_id: int = None):
    """单条生成测试用例（流式响应）"""
    try:
        # 尝试获取需求详情
        req = requirement_service.get_requirement_by_id(req_id)
        if not req:
            raise HTTPException(status_code=404, detail="未找到对应的需求")

        return StreamingResponse(
            test_case_service.generate_cases(
                req_id,
                req['feature_name'],
                req['description'],
                target_count=count,
                mode=mode,
                domain=domain,
                prompt_id=prompt_id
            ),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")


@router.post("/batch_generate_stream")
async def batch_generate_requirements_stream(body: BatchGenerateRequest):
    """批量生成测试用例（流式响应）"""
    try:
        if not body.ids or len(body.ids) == 0:
            raise HTTPException(400, "请选择至少一个功能点")
        return StreamingResponse(
            test_case_service.batch_generate_cases(body.ids, body.count),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量生成测试用例失败: {str(e)}")


@router.get("/{req_id}/cases")
def get_cases_by_req(req_id: int):
    """获取指定需求的测试用例列表"""
    try:
        # 这个接口如果你还在用，需要确保 db_tools 或 case_db 里有对应方法
        # 建议统一使用 list_cases 接口
        result = test_case_service.get_cases(1, 100, req_id=req_id)
        return result['items']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取需求相关用例失败: {str(e)}")
