#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
services目录初始化文件
"""

from .case_service import CaseService
from .requirement_service import RequirementService
from .project_service import ProjectService

# 实例化服务
test_case_service = CaseService()
requirement_service = RequirementService()
project_service = ProjectService()
