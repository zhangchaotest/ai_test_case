#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
数据模型定义
使用 Pydantic 定义 API 请求和响应的数据结构，确保数据类型安全和自动验证。
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, TypeVar, Generic


# =========================================================
# 需求相关模型
# =========================================================
class Requirement(BaseModel):
    """
    需求功能点模型
    对应 functional_points 表
    """
    id: int
    module_name: str
    feature_name: str
    description: str
    priority: str
    case_count: int = 0  # 统计该需求下有多少用例 (非数据库字段，查询时聚合)


# =========================================================
# 测试用例相关模型
# =========================================================
class TestCaseResponse(BaseModel):
    """
    测试用例响应模型
    用于 API 返回测试用例详情
    """
    id: int
    requirement_id: int
    case_title: str
    pre_condition: Optional[str] = ""
    steps: List[Dict[str, Any]] = []  # 测试步骤，默认为空列表
    expected_result: Optional[str] = ""

    # 允许这些字段为空，提供默认值
    priority: Optional[str] = "P1"
    case_type: Optional[str] = "Functional"
    test_data: Optional[Dict[str, Any]] = {}
    status: Optional[str] = "Active"


# =========================================================
# 通用分页模型
# =========================================================
T = TypeVar('T')

class PageResponse(BaseModel, Generic[T]):
    """
    通用分页响应结构
    """
    total: int          # 总记录数
    page: int           # 当前页码
    size: int           # 每页大小
    items: List[T]      # 数据列表
