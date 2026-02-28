#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
API路由初始化
"""

from fastapi import APIRouter

# 创建主路由
api_router = APIRouter()

# 导入并注册子路由
from .analysis import router as analysis_router
from .cases import router as cases_router
from .export import router as export_router
from .projects import router as projects_router
from .requirements import router as requirements_router
from .prompts import router as prompts_router
from .config import router as config_router

# 注册子路由
api_router.include_router(analysis_router, tags=["analysis"])
api_router.include_router(cases_router, prefix="/cases", tags=["cases"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(requirements_router, prefix="/requirements", tags=["requirements"])
api_router.include_router(prompts_router, tags=["prompts"])
api_router.include_router(config_router, tags=["config"])
