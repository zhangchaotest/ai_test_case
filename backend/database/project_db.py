#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：project_db.py
@Author  ：张超
@Date    ：2025/12/22 00:01
@Desc    ：
"""
#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File    ：project_db.py
@Desc    ：项目 (Projects) 相关的数据库操作
"""
import sqlite3
from .base import get_conn

def create_project(name: str, desc: str = ""):
    """创建新项目"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO projects (project_name, description) VALUES (?, ?)", (name, desc))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return -1 # 项目名重复
    finally:
        conn.close()

def get_all_projects():
    """获取所有项目列表"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_project_by_id(project_id: int):
    """获取单条项目详情"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None