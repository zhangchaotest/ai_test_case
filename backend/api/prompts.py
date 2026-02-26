#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
提示词管理 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.database.prompt_db import (
    get_prompts, get_prompt_by_id, create_prompt, update_prompt, delete_prompt
)

# 创建路由器
router = APIRouter(prefix="/prompts", tags=["prompts"])


# 数据模型
class PromptBase(BaseModel):
    name: str
    content: str
    domain: str
    type: str
    description: Optional[str] = ""


class PromptCreate(PromptBase):
    pass


class PromptUpdate(PromptBase):
    pass


class PromptResponse(PromptBase):
    id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[PromptResponse])
def list_prompts(domain: Optional[str] = None, type: Optional[str] = None):
    """获取提示词列表"""
    try:
        prompts = get_prompts(domain, type)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提示词列表失败: {str(e)}")


@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int):
    """根据ID获取提示词"""
    try:
        prompt = get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提示词失败: {str(e)}")


@router.post("", response_model=PromptResponse)
def create_prompt_api(body: PromptCreate):
    """创建提示词"""
    try:
        prompt_id = create_prompt(body.model_dump())
        prompt = get_prompt_by_id(prompt_id)
        if not prompt:
            raise HTTPException(status_code=500, detail="创建提示词失败")
        return prompt
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建提示词失败: {str(e)}")


@router.put("/{prompt_id}", response_model=PromptResponse)
def update_prompt_api(prompt_id: int, body: PromptUpdate):
    """更新提示词"""
    try:
        # 检查提示词是否存在
        existing_prompt = get_prompt_by_id(prompt_id)
        if not existing_prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")
        
        # 更新提示词
        success = update_prompt(prompt_id, body.model_dump())
        if not success:
            raise HTTPException(status_code=500, detail="更新提示词失败")
        
        # 返回更新后的提示词
        updated_prompt = get_prompt_by_id(prompt_id)
        return updated_prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新提示词失败: {str(e)}")


@router.delete("/{prompt_id}")
def delete_prompt_api(prompt_id: int):
    """删除提示词"""
    try:
        # 检查提示词是否存在
        existing_prompt = get_prompt_by_id(prompt_id)
        if not existing_prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")
        
        # 删除提示词
        success = delete_prompt(prompt_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除提示词失败")
        
        return {"status": "success", "message": "提示词删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除提示词失败: {str(e)}")
