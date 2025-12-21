#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：init_db.py
@Author  ：张超
@Date    ：2025/12/22 00:06
@Desc    ：
"""
# !/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File    ：init_db.py
@Desc    ：数据库初始化与表结构管理
"""
import sqlite3
from .base import get_conn, DB_PATH


def init_tables():
    """初始化所有表结构"""
    conn = get_conn()
    cursor = conn.cursor()

    print("⚙️ [DB Init] 正在检查并初始化数据库表结构...")

    # 1. 项目表 (Projects)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS projects
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       project_name
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       description
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # 2. 需求功能点表 (Functional Points)
    # 包含 project_id (关联项目) 和 source_content (原始需求)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS functional_points
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       project_id
                       INTEGER,
                       module_name
                       TEXT,
                       feature_name
                       TEXT,
                       description
                       TEXT,
                       priority
                       TEXT,
                       source_content
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # 3. 测试用例表 (Test Cases)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS test_cases
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       requirement_id
                       INTEGER,
                       case_title
                       TEXT,
                       pre_condition
                       TEXT,
                       steps
                       TEXT,
                       expected_result
                       TEXT,
                       priority
                       TEXT
                       DEFAULT
                       'P1',
                       case_type
                       TEXT
                       DEFAULT
                       'Functional',
                       test_data
                       TEXT,
                       status
                       TEXT
                       DEFAULT
                       'Draft',
                       version
                       INTEGER
                       DEFAULT
                       1,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # --- 自动迁移逻辑 (Migration) ---
    # 防止旧数据库缺少字段导致报错
    try:
        cursor.execute("ALTER TABLE functional_points ADD COLUMN project_id INTEGER")
        print("   -> 补丁: functional_points 增加 project_id")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE functional_points ADD COLUMN source_content TEXT")
        print("   -> 补丁: functional_points 增加 source_content")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("✅ [DB Init] 数据库初始化完成")


def seed_data():
    """插入默认的种子数据 (可选)"""
    conn = get_conn()
    cursor = conn.cursor()

    # 检查是否需要插入默认项目
    cursor.execute("SELECT count(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO projects (project_name, description) VALUES (?, ?)",
                       ("默认项目", "系统自动创建的默认演示项目"))
        print("🌱 [DB Seed] 已插入默认项目")

    conn.commit()
    conn.close()