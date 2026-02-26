# !/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File    ：project_db.py
@Desc    ：项目 (Projects) 相关的数据库操作
"""
import sqlite3
from .db_base import DatabaseBase


class ProjectDB(DatabaseBase):
    """项目数据库操作类"""
    
    def create_project(self, name: str, desc: str = ""):
        """创建新项目"""
        sql = "INSERT INTO projects (project_name, description) VALUES (?, ?)"
        try:
            return self.execute_insert(sql, (name, desc))
        except sqlite3.IntegrityError:
            return -1  # 项目名重复
    
    def get_all_projects(self):
        """获取所有项目列表"""
        return self.execute_query("SELECT * FROM projects ORDER BY id DESC")
    
    def get_project_by_id(self, project_id: int):
        """获取单条项目详情"""
        return self.get_by_id("projects", project_id)


# 实例化
project_db = ProjectDB()


# 保持向后兼容
def create_project(name: str, desc: str = ""):
    return project_db.create_project(name, desc)

def get_all_projects():
    return project_db.get_all_projects()

def get_project_by_id(project_id: int):
    return project_db.get_project_by_id(project_id)
