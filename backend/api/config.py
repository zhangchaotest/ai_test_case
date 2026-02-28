#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
功能开关配置API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config.feature_config import FEATURE_CONFIG

router = APIRouter()


class FeatureConfig(BaseModel):
    use_knowledge: bool
    use_llm: bool
    use_test_dimension: bool
    use_context_manager: bool


@router.get("/config/feature")
def get_feature_config():
    """
    获取功能开关配置
    """
    return FEATURE_CONFIG


@router.post("/config/feature")
def update_feature_config(config: FeatureConfig):
    """
    更新功能开关配置
    """
    try:
        # 更新配置
        FEATURE_CONFIG.update(config.model_dump())
        
        # 保存到文件
        with open("backend/config/feature_config.py", "w", encoding="utf-8") as f:
            f.write("# 功能开关配置文件\n\n")
            f.write("# 功能开关配置\n")
            f.write("FEATURE_CONFIG = {\n")
            for key, value in FEATURE_CONFIG.items():
                # 获取注释
                comment = ""
                if key == "use_knowledge":
                    comment = "# 是否使用Dify知识库"
                elif key == "use_llm":
                    comment = "# 是否使用LLM模型"
                elif key == "use_test_dimension":
                    comment = "# 是否使用测试维度分析"
                elif key == "use_context_manager":
                    comment = "# 是否使用上下文管理器"
                f.write(f"    \"{key}\": {value}, {comment}\n")
            f.write("}\n")
        
        return {"status": "success", "message": "配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")
