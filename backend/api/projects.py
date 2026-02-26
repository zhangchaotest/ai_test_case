#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
项目管理 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import project_service

# 创建路由器
router = APIRouter(prefix="", tags=["projects"])

# 数据模型
class ProjectCreate(BaseModel):
    name: str
    description: str = ""


@router.get("")
def get_projects():
    """获取项目列表"""
    try:
        projects = project_service.get_all_projects()
        return {"items": projects}  # 包装为{items: [...]}格式
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.post("")
def create_project(body: ProjectCreate):
    """创建新项目"""
    try:
        project_id = project_service.create_project(body.name, body.description)
        return {"status": "success", "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")
