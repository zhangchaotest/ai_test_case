#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：requirement_db.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：
"""
from typing import Dict, Any

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

def save_analyzed_point(data: Dict[str, Any]) -> str:
    """
    保存分析出的功能点 (Agent调用)
    """
    conn = get_conn()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO functional_points 
            (project_id, module_name, feature_name, description, priority, source_content) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('project_id'),
            data.get('module_name', '未分类模块'),
            data.get('feature_name', '未命名功能'),
            data.get('description', ''),
            data.get('priority', 'P1'),
            data.get('source_content', '') # 记录原始需求
        )
        cursor.execute(sql, params)
        conn.commit()
        return f"ID: {cursor.lastrowid}"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()


def save_breakdown_item(data: Dict[str, Any]) -> str:
    """
    保存需求分解项 (Agent调用)
    """
    conn = get_conn()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO requirement_breakdown 
            (project_id, module_name, feature_name, description, acceptance_criteria,
             requirement_type, priority, confidence_score, review_status, review_comments, source_content) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # 🔥 核心修改：
        # 1. 确保 feature_name 有值，如果是 '未命名'，尝试从 description 截取
        feat_name = data.get('feature_name', '未命名')
        if feat_name == '未命名' and data.get('description'):
             feat_name = data['description'][:10] # 简略处理
        params = (
            data.get('project_id'),
            data.get('module_name', '通用'),
            feat_name,
            data.get('description', ''),
            data.get('acceptance_criteria', ''),
            data.get('requirement_type', '功能需求'),
            data.get('priority', 'P1'),
            data.get('confidence_score', 0.8),
            # data.get('review_status', 'Pending'),
            'Pending',
            data.get('review_comments', ''),
            data.get('source_content', '')
        )
        cursor.execute(sql, params)
        conn.commit()
        return f"ID: {cursor.lastrowid}"
    finally:
        conn.close()


def get_breakdown_page(page=1, size=10, project_id=None, feature_name=None, status=None):
    """
    分页查询 (供前端 ProTable 使用)
    :param status:
    :param page:
    :param size:
    :param project_id:
    :param feature_name:
    :return:
    """
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if project_id:
        where_clauses.append("project_id = ?")
        params.append(project_id)
    if feature_name:
        where_clauses.append("feature_name LIKE ?")
        params.append(f"%{feature_name}%")

    if status:
        where_clauses.append("review_status = ?")
        params.append(status)

    where_str = " AND ".join(where_clauses)

    base_sql = f"SELECT * FROM requirement_breakdown WHERE {where_str} ORDER BY id DESC"
    count_sql = f"SELECT COUNT(*) FROM requirement_breakdown WHERE {where_str}"

    result = execute_page_query(cursor, base_sql, count_sql, tuple(params), page, size)
    conn.close()
    return result

def update_breakdown_item(item_id: int, data: Dict[str, Any]):
    """
    更新功能点 (人工编辑用)
    :param item_id:
    :param data:
    :return:
    """
    conn = get_conn()
    cursor = conn.cursor()
    try:
        # 只允许更新部分核心字段
        sql = """
            UPDATE requirement_breakdown 
            SET module_name=?, feature_name=?, description=?, acceptance_criteria=?, priority=?
            WHERE id=?
        """
        params = (
            data['module_name'],
            data['feature_name'],
            data['description'],
            data['acceptance_criteria'],
            data['priority'],
            item_id
        )
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"Update Error: {e}")
        return False
    finally:
        conn.close()


def update_breakdown_status(item_id: int, new_status: str):
    """更新状态，如果状态为 Pass，则同步到 functional_points"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        # 1. 更新当前表状态
        cursor.execute("UPDATE requirement_breakdown SET review_status = ? WHERE id = ?", (new_status, item_id))

        # 2. 如果是 Pass，执行同步逻辑
        if new_status == 'Pass':
            # 先查出这条数据
            cursor.execute("SELECT * FROM requirement_breakdown WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                # 转换 Row 为字典 (假设 base.py 里设了 row_factory)
                data = dict(row)

                # 插入到 functional_points (字段映射)
                # 注意：这里需要确保 functional_points 有对应字段，或者把多余字段拼接到 description
                insert_sql = """
                             INSERT INTO functional_points
                             (project_id, module_name, feature_name, description, priority, source_content)
                             VALUES (?, ?, ?, ?, ?, ?) \
                             """
                # 将 验收标准 拼接到 描述 中，因为 functional_points 可能没有 acceptance_criteria 字段
                full_desc = f"{data['description']}\n\n【验收标准】\n{data['acceptance_criteria']}"

                insert_params = (
                    data['project_id'],
                    data['module_name'],
                    data['feature_name'],
                    full_desc,
                    data['priority'],
                    data['source_content']
                )
                cursor.execute(insert_sql, insert_params)
                print(f"✅ [Sync] 拆解项 ID:{item_id} 已同步至功能点表")

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Status Update Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


