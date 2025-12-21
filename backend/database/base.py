#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：base.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：基础类
"""

import sqlite3
import json

DB_PATH = "requirements.db"


def get_conn():
    """获取数据库连接 (Row Factory)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让结果可以通过 dict 方式访问
    return conn


def safe_json_loads(json_str):
    """通用的 JSON 解析工具"""
    if not json_str: return None
    cleaned = json_str.strip()
    if cleaned.startswith("```"):  # 去除 markdown 标记
        parts = cleaned.split("\n", 1)
        if len(parts) > 1: cleaned = parts[1]
        if cleaned.strip().endswith("```"): cleaned = cleaned.strip()[:-3]
    try:
        return json.loads(cleaned)
    except:
        return None


def execute_page_query(cursor, base_sql, count_sql, params, page, size):
    """
    [通用] 分页查询执行器
    """
    offset = (page - 1) * size

    # 1. 查总数
    cursor.execute(count_sql, params)
    total_row = cursor.fetchone()
    total = total_row[0] if total_row else 0

    # 2. 查数据
    final_sql = f"{base_sql} LIMIT ? OFFSET ?"
    final_params = params + (size, offset)

    cursor.execute(final_sql, final_params)
    rows = [dict(row) for row in cursor.fetchall()]

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": rows
    }