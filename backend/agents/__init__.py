#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：__init__.py.py
@Author  ：张超
@Date    ：2025/12/15 17:48
@Desc    ：
"""
# backend/agents/__init__.py

# 从子模块导出主要的服务函数，方便外部调用
# 例如: from backend.agents import run_case_generation_stream
from .case_agent import run_case_generation_stream, run_batch_functional_generation_stream
from .requirement_agent import run_requirement_analysis_stream
from .prompt_manager import PromptManager
from .test_dimension import TestDimensionManager
from .context_manager import ContextManager

__all__ = [
    'run_case_generation_stream',
    'run_batch_functional_generation_stream',
    'run_requirement_analysis_stream',
    'PromptManager',
    'TestDimensionManager',
    'ContextManager'
]
