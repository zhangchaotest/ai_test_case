#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：base.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：基础类
"""
import ast
import sqlite3
import json

DB_PATH = "requirements.db"


def get_conn():
    """获取数据库连接 (Row Factory)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让结果可以通过 dict 方式访问
    return conn


def safe_json_loads(json_str):
    """
    通用的 JSON 解析工具 (增强版)
    兼容：标准 JSON (双引号)、Markdown 包裹的代码块、Python 字典字符串 (单引号)
    """
    if not json_str:
        return []  # 空值直接返回空列表

    # 1. 基础清洗
    cleaned = json_str.strip()

    # 2. 去除 Markdown 标记 (```json ... ```)
    if cleaned.startswith("```"):
        parts = cleaned.split("\n", 1)
        if len(parts) > 1:
            cleaned = parts[1]
        # 去掉结尾的 ```
        if cleaned.strip().endswith("```"):
            cleaned = cleaned.strip()[:-3].strip()

    # 3. 尝试标准 JSON 解析 (最快，最标准)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass  # 解析失败，尝试下一个方案

    # 4. 🔥 尝试 Python 字面量解析 (解决单引号问题)
    # 很多时候 LLM 会存成 [{'step_id': 1}] 这种单引号格式，json.loads 会报错
    try:
        return ast.literal_eval(cleaned)
    except Exception as e:
        # 5. 如果都失败了，打印出来看看是啥怪东西
        print(f"❌ [JSON Parse Error] 解析失败，原始数据: {json_str[:100]}... 错误: {e}")
        return []  # 解析不了就返回空，防止前端报错


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