#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
项目管理服务
"""

from backend.database.project_db import get_all_projects, create_project as db_create_project


class ProjectService:
    """项目管理服务类"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def get_all_projects(self):
        """
        获取所有项目
        
        :return: 项目列表
        """
        return get_all_projects()
    
    def create_project(self, name: str, description: str = ""):
        """
        创建新项目
        
        :param name: 项目名称
        :param description: 项目描述
        :return: 项目ID
        """
        return db_create_project(name, description)
