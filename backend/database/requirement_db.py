#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：requirement_db.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：
"""
from .base import get_conn, execute_page_query


def get_requirements_page(page=1, size=10, feature_name=None, priority=None):
    conn = get_conn()
    cursor = conn.cursor()

    # 1. 构建动态 SQL
    where_clauses = ["1=1"]
    params = []

    if feature_name:
        where_clauses.append("feature_name LIKE ?")
        params.append(f"%{feature_name}%")

    if priority:
        where_clauses.append("priority = ?")
        params.append(priority)

    where_str = " AND ".join(where_clauses)

    # 2. 定义 SQL 模板
    base_sql = f"""
        SELECT fp.*, 
        (SELECT COUNT(*) FROM test_cases tc WHERE tc.requirement_id = fp.id) as case_count 
        FROM functional_points fp 
        WHERE {where_str}
        ORDER BY fp.id DESC
    """

    count_sql = f"SELECT COUNT(*) FROM functional_points WHERE {where_str}"

    # 3. 调用通用分页
    result = execute_page_query(cursor, base_sql, count_sql, tuple(params), page, size)

    conn.close()
    return result


def get_by_id(req_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functional_points WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None