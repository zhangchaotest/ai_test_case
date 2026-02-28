#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File    ：project_db.py
@Desc    ：项目 (Projects) 相关的数据库操作
负责项目的创建、查询等基础管理功能。
"""
import sqlite3
from .db_base import DatabaseBase


class ProjectDB(DatabaseBase):
    """
    项目数据库操作类
    继承自 DatabaseBase
    """
    
    def create_project(self, name: str, desc: str = ""):
        """
        创建新项目
        
        :param name: 项目名称 (必须唯一)
        :param desc: 项目描述
        :return: 新项目的 ID，如果名称重复返回 -1
        """
        sql = "INSERT INTO projects (project_name, description) VALUES (?, ?)"
        try:
            return self.execute_insert(sql, (name, desc))
        except sqlite3.IntegrityError:
            # 捕获唯一约束冲突异常
            return -1  # 项目名重复
    
    def get_all_projects(self):
        """
        获取所有项目列表
        按 ID 倒序排列
        :return: 项目列表 List[Dict]
        """
        return self.execute_query("SELECT * FROM projects ORDER BY id DESC")
    
    def get_project_by_id(self, project_id: int):
        """
        根据 ID 获取单条项目详情
        
        :param project_id: 项目 ID
        :return: 项目详情字典
        """
        return self.get_by_id("projects", project_id)


# 实例化全局对象
project_db = ProjectDB()


# =========================================================
# 兼容性封装 (保持向后兼容，供旧代码调用)
# =========================================================
def create_project(name: str, desc: str = ""):
    return project_db.create_project(name, desc)

def get_all_projects():
    return project_db.get_all_projects()

def get_project_by_id(project_id: int):
    return project_db.get_project_by_id(project_id)
