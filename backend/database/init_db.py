#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File    ：init_db.py
@Desc    ：数据库初始化与表结构管理 (含字段注释)
"""
import sqlite3
from .base import get_conn, DB_PATH


def init_tables():
    """初始化所有表结构"""
    conn = get_conn()
    cursor = conn.cursor()

    print("⚙️ [DB Init] 正在检查并初始化数据库表结构...")

    # --------------------------------------------------------
    # 1. 项目表 (Projects)
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 项目ID (主键)
            project_name TEXT NOT NULL UNIQUE,      -- 项目名称 (唯一)
            description TEXT,                       -- 项目描述
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
        )
    """)

    # --------------------------------------------------------
    # 2. 需求功能点表 (Functional Points)
    # 说明：这是审核通过后，正式入库的功能点，用于生成测试用例
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS functional_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 功能点ID (主键)
            project_id INTEGER,                     -- 关联的项目ID
            module_name TEXT,                       -- 所属模块名称
            feature_name TEXT,                      -- 功能点名称
            description TEXT,                       -- 功能点详细描述
            priority TEXT,                          -- 优先级 (P0/P1/P2)
            source_content TEXT,                    -- 原始需求内容 (用于追溯)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
        )
    """)

    # --------------------------------------------------------
    # 3. 测试用例表 (Test Cases)
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- 用例ID (主键)
            requirement_id INTEGER,                 -- 关联的功能点ID
            case_title TEXT,                        -- 用例标题
            pre_condition TEXT,                     -- 前置条件
            steps TEXT,                             -- 测试步骤 (JSON字符串: List[Dict])
            expected_result TEXT,                   -- 预期结果
            priority TEXT DEFAULT 'P1',             -- 优先级 (P0/P1/P2)
            case_type TEXT DEFAULT 'Functional',    -- 用例类型 (Functional/Negative/Boundary/Performance)
            test_data TEXT,                         -- 测试数据 (JSON字符串: Dict)
            status TEXT DEFAULT 'Draft',            -- 状态 (Draft:草稿, Active:有效, Deprecated:废弃)
            version INTEGER DEFAULT 1,              -- 版本号
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
        )
    """)

    # --------------------------------------------------------
    # 4. 需求拆解详情表 (Requirement Breakdown)
    # 说明：这是AI分析后的中间态数据，用于人工评审
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requirement_breakdown (
                                                             id                  INTEGER PRIMARY KEY AUTOINCREMENT,  -- 拆解项ID (主键)
                                                             project_id          INTEGER,                            -- 关联的项目ID
                                                             module_name         TEXT,                               -- 所属模块
                                                             feature_name        TEXT,                               -- 功能名称
                                                             description         TEXT,                               -- 功能描述
                                                             acceptance_criteria TEXT,                               -- 验收标准 (最重要的字段，通常存为 JSON 列表字符串)
                                                             requirement_type    TEXT,                               -- 需求类型 (新增/优化/Bug)
                                                             priority            TEXT,                               -- 优先级 (P0/P1/P2)
                                                             confidence_score    REAL,                               -- AI置信度评分 (0.0 - 1.0)
                                                             review_status       TEXT,                               -- 评审状态 (Pending:待审, Pass:通过, Reject:拒绝, Discard:废弃)
                                                             review_comments     TEXT,                               -- AI或人工的评审意见
                                                             source_content      TEXT,                               -- 原始需求片段摘录
                                                             created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
        )
    """)

    # --------------------------------------------------------
    # 5. 自动迁移逻辑 (Migration)
    # 防止旧数据库缺少字段导致报错
    # --------------------------------------------------------
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


    try:
        cursor.execute("ALTER TABLE test_cases ADD COLUMN quality_score REAL")
        print("   -> 补丁: test_cases 增加 quality_score")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE test_cases ADD COLUMN review_comments TEXT")
        print("   -> 补丁: test_cases 增加 review_comments")
    except sqlite3.OperationalError: pass
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