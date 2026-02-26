#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试用例管理 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from backend.services import test_case_service

# 创建路由器
router = APIRouter(prefix="", tags=["cases"])

# 数据模型
class BatchUpdateStatusRequest(BaseModel):
    ids: List[int]
    status: str


@router.get("")
def list_cases(
        page: int = 1,
        size: int = 10,
        req_id: int = None,
        status: str = None
):
    """获取测试用例列表"""
    try:
        return test_case_service.get_cases(page, size, req_id=req_id, status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试用例列表失败: {str(e)}")


@router.put("/batch_status")
def batch_update_case_status(body: BatchUpdateStatusRequest):
    """批量更新测试用例状态"""
    try:
        if not body.ids or len(body.ids) == 0:
            raise HTTPException(400, "请选择至少一个测试用例")
        
        success = test_case_service.batch_update_case_status(body.ids, body.status)
        if success:
            return {"status": "success", "message": f"已更新 {len(body.ids)} 个测试用例的状态为 {body.status}"}
        raise HTTPException(500, "状态更新失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量更新状态失败: {str(e)}")
