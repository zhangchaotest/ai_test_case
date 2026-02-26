#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试用例导出 API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.services import test_case_service

# 创建路由器
router = APIRouter(prefix="", tags=["export"])


@router.get("")
def export_cases(req_id: int = None, status: str = None, format: str = "excel"):
    """导出测试用例"""
    try:
        # 获取导出数据
        cases = test_case_service.get_cases_for_export(req_id=req_id, status=status)
        
        if not cases:
            raise HTTPException(404, "没有找到符合条件的测试用例")
        
        # 根据格式导出
        if format == "excel":
            # 这里应该实现Excel导出逻辑
            # 暂时返回JSON格式
            import json
            return Response(
                content=json.dumps(cases, ensure_ascii=False),
                media_type="application/json"
            )
        elif format == "xmind":
            # 这里应该实现XMind导出逻辑
            import json
            return Response(
                content=json.dumps(cases, ensure_ascii=False),
                media_type="application/json"
            )
        else:
            raise HTTPException(400, "不支持的导出格式")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出测试用例失败: {str(e)}")
