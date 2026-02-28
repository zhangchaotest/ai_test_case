#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
项目管理服务层
负责项目的创建和查询业务逻辑。
"""

from backend.database.project_db import get_all_projects, create_project as db_create_project


class ProjectService:
    """
    项目管理服务类
    """
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def get_all_projects(self):
        """
        获取所有项目列表
        
        :return: 项目列表 List[Dict]
        """
        return get_all_projects()
    
    def create_project(self, name: str, description: str = ""):
        """
        创建新项目
        
        :param name: 项目名称
        :param description: 项目描述
        :return: 新项目 ID，如果名称重复返回 -1
        """
        return db_create_project(name, description)
