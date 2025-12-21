#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：case_db.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：
"""
from typing import Dict, Any

# backend/database/case_db.py

from .base import get_conn, execute_page_query, safe_json_loads
import json


def get_cases_page(page=1, size=10, req_id=None, title=None):
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if req_id:
        where_clauses.append("requirement_id = ?")
        params.append(req_id)

    if title:
        where_clauses.append("case_title LIKE ?")
        params.append(f"%{title}%")

    where_str = " AND ".join(where_clauses)

    base_sql = f"SELECT * FROM test_cases WHERE {where_str} ORDER BY id DESC"
    count_sql = f"SELECT COUNT(*) FROM test_cases WHERE {where_str}"

    # 1. 执行分页查询
    result = execute_page_query(cursor, base_sql, count_sql, tuple(params), page, size)

    # 2. [特有逻辑] 处理 JSON 字段 (steps, test_data)
    for item in result['items']:
        item['steps'] = safe_json_loads(item.get('steps')) or []
        item['test_data'] = safe_json_loads(item.get('test_data')) or {}

    conn.close()
    return result


def save_case(data: Dict[str, Any]) -> str:
    """
    保存单条用例 (供 Agent 或 业务逻辑调用)
    :param data: 包含用例信息的字典，必须包含 requirement_id, case_title 等
    """
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 1. 序列化复杂字段 (List/Dict -> JSON String)
        # ensure_ascii=False 保证中文正常显示，而不是 \uXXXX

        # 处理 steps: 如果是列表转JSON，如果是空则存空数组
        steps_raw = data.get('steps', [])
        if isinstance(steps_raw, list):
            steps_json = json.dumps(steps_raw, ensure_ascii=False)
        else:
            # 如果传进来的已经是字符串（极少情况），直接用
            steps_json = str(steps_raw)

        # 处理 test_data: 同理
        test_data_raw = data.get('test_data', {})
        if isinstance(test_data_raw, dict):
            test_data_json = json.dumps(test_data_raw, ensure_ascii=False)
        else:
            test_data_json = str(test_data_raw)

        # 2. 准备插入数据的 SQL
        sql = """
              INSERT INTO test_cases (requirement_id, \
                                      case_title, \
                                      pre_condition, \
                                      steps, \
                                      expected_result, \
                                      priority, \
                                      case_type, \
                                      test_data, \
                                      status) \
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) \
              """

        # 3. 提取参数 (使用 .get() 提供默认值，防止 KeyError)
        params = (
            data['requirement_id'],  # 必填，如果缺了直接抛错
            data.get('case_title', '未命名用例'),  # 必填，缺了给默认值
            data.get('pre_condition', '无'),
            steps_json,  # 存 JSON 字符串
            data.get('expected_result', '无'),
            data.get('priority', 'P1'),
            data.get('case_type', 'Functional'),
            test_data_json,  # 存 JSON 字符串
            'Active'  # 默认为生效状态
        )

        # 4. 执行插入
        cursor.execute(sql, params)
        conn.commit()

        # 获取新生成的 ID
        new_id = cursor.lastrowid
        print(f"✅ [DB] 用例保存成功 ID: {new_id}")
        return str(new_id)

    except Exception as e:
        print(f"❌ [DB Error] 保存用例失败: {str(e)}")
        # 如果是必须抛出异常让上层处理，可以 raise e
        # 这里返回 -1 表示失败
        return "-1"

    finally:
        # 5. 确保连接关闭
        if conn:
            conn.close()


def get_existing_titles(req_id: int):
    """获取指定需求下所有已存在的用例标题"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT case_title FROM test_cases WHERE requirement_id = ?", (req_id,))
    rows = cursor.fetchall()
    conn.close()
    # 返回列表: ['登录成功', '密码错误', ...]
    return [row['case_title'] for row in rows]