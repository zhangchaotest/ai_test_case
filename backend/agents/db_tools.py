#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：db_tools.py
@Author  ：张超
@Date    ：2025/12/17 16:52
@Desc    ：
"""
import json
# db_tools.py
import sqlite3
from typing import Annotated
from typing import Annotated, List, Dict


# 1. 初始化数据库表 (为了演示简单，用 SQLite)
def init_db():
    conn = sqlite3.connect("../requirements.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS functional_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT,
            feature_name TEXT,
            description TEXT,
            priority TEXT
        )
    """)
    # 升级后的测试用例表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases
        (
           id              INTEGER PRIMARY KEY AUTOINCREMENT,
           requirement_id  INTEGER,
        
           -- 基础信息
           case_title      TEXT NOT NULL,
           pre_condition   TEXT,
           steps           TEXT,                           -- 存 JSON Array
           expected_result TEXT,
        
           -- 🔥 新增核心字段
           priority        TEXT      DEFAULT 'P1',         -- P0, P1, P2
           case_type       TEXT      DEFAULT 'Functional', -- Functional, Negative...
           test_data       TEXT,                           -- 存 JSON Object (测试数据)
        
           -- 🔥 新增管理字段
           status          TEXT      DEFAULT 'Active',     -- Active, Deprecated
           version         INTEGER   DEFAULT 1,
        
           created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    conn.commit()
    conn.close()

# 初始化一下 (实际项目中可以放在启动脚本里)
init_db()

# 2. 定义给 Agent 使用的工具函数
# 🔥 关键：必须使用 Type Hints (类型提示) 和 Docstring (注释)，
# 这样大模型才能知道如何使用这个工具。
def save_functional_point(
    module_name: Annotated[str, "所属模块名称，例如：用户中心、订单系统"],
    feature_name: Annotated[str, "功能点名称，例如：用户登录"],
    description: Annotated[str, "详细的功能描述和验收标准"],
    priority: Annotated[str, "优先级，例如：P0, P1, P2"] = "P1"
) -> str:
    """
    将拆分出的单个功能点保存到数据库中。
    """
    try:
        conn = sqlite3.connect("../requirements.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO functional_points (module_name, feature_name, description, priority) VALUES (?, ?, ?, ?)",
            (module_name, feature_name, description, priority)
        )
        conn.commit()
        point_id = cursor.lastrowid
        conn.close()
        return f"✅ 成功保存功能点：{feature_name} (ID: {point_id})"
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"

# --- 新增工具函数 ---

def get_all_requirements() -> List[Dict]:
    """[给主程序用] 获取所有待测试的功能点"""
    conn = sqlite3.connect("../requirements.db")
    conn.row_factory = sqlite3.Row # 让结果像字典一样访问
    cursor = conn.cursor()
    # 使用 SQL 过滤：只选出那些在 test_cases 表里找不到 ID 的需求
    query = """
        SELECT fp.* 
        FROM functional_points fp
        WHERE fp.id NOT IN (
            SELECT DISTINCT requirement_id FROM test_cases
        )
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_test_cases(req_id=None):
    conn = sqlite3.connect("../requirements.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if req_id:
        cursor.execute("SELECT * FROM test_cases WHERE requirement_id = ? ORDER BY id DESC", (req_id,))
    else:
        cursor.execute("SELECT * FROM test_cases ORDER BY id DESC")

    rows = []
    for row in cursor.fetchall():
        item = dict(row)
        # 🔥 关键：在取出时把 JSON 字符串转回 Python 对象，方便前端直接用
        if item.get('steps'):
            try:
                item['steps'] = json.loads(item['steps'])
            except:
                item['steps'] = []
        if item.get('test_data'):
            try:
                item['test_data'] = json.loads(item['test_data'])
            except:
                item['test_data'] = {}
        rows.append(item)
    conn.close()
    return rows

def save_verified_test_case(
    requirement_id: int,
    case_title: Annotated[str, "用例标题"],
    pre_condition: Annotated[str, "前置条件"],
    steps: Annotated[List[Dict], "JSON格式的步骤"],
    expected_result: Annotated[str, "预期结果"],
    # 🔥 新增参数
    priority: Annotated[str, "优先级 (P0-P3)"],
    case_type: Annotated[str, "用例类型 (Functional/Negative/Boundary)"],
    test_data: Annotated[Dict, "测试数据键值对，如 {'user': 'admin'}"] = {}
) -> str:
    """
    [给评审Agent用] 将评审通过的测试用例保存到数据库。
    """
    try:
        # 1. 将列表转换为 JSON 字符串存库
        # ensure_ascii=False 保证存进去的是中文，不是 \uXXXX
        steps_json = json.dumps(steps, ensure_ascii=False)

        conn = sqlite3.connect("../requirements.db")
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO test_cases
                   (requirement_id, case_title, pre_condition, steps, expected_result,priority,case_type,test_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (requirement_id, case_title, pre_condition, steps_json, expected_result,priority,case_type,test_data)
        )
        conn.commit()
        cid = cursor.lastrowid
        conn.close()
        return f"✅ 用例已入库 (ID: {cid})"
    except Exception as e:
        return f"❌ 入库失败: {e}"