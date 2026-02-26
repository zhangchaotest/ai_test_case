#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：requirement_db.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：
"""
import json
from typing import Dict, Any, List

from backend.database.base import execute_page_query
from backend.database.db_base import DatabaseBase


class RequirementDB(DatabaseBase):
    """需求数据库操作类"""
    
    def get_requirements_page(self, page=1, size=10, feature_name=None, priority=None):
        """分页获取功能点"""
        with self.get_connection() as conn:
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

            return result
    
    def get_requirement_by_id(self, req_id: int):
        """根据ID获取功能点"""
        return self.get_by_id("functional_points", req_id)
    
    def save_analyzed_point(self, data: Dict[str, Any]) -> str:
        """
        保存分析出的功能点 (Agent调用)
        """
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
                data.get('source_content', '')  # 记录原始需求
            )
            new_id = self.execute_insert(sql, params)
            return f"ID: {new_id}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def save_breakdown_item(self, data: Dict[str, Any]) -> str:
        """保存需求拆解项"""
        try:
            # 1. 智能解包参数 (防止嵌套)
            actual_data = data
            if 'data' in data and isinstance(data['data'], dict):
                actual_data = data['data']

            print(f"🐛 [DEBUG SAVE] 正在保存: {actual_data.get('feature_name', '未命名')}")

            sql = """
                  INSERT INTO requirement_breakdown
                  (project_id, module_name, feature_name, description, acceptance_criteria,
                   requirement_type, priority, confidence_score, review_status, review_comments, source_content)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                  """

            # --- 🔥 核心修复：处理验收标准 (List -> JSON String) ---
            ac_raw = actual_data.get('acceptance_criteria', '')
            if isinstance(ac_raw, list):
                # 如果是列表，转成 JSON 字符串存入
                ac_str = json.dumps(ac_raw, ensure_ascii=False)
            else:
                # 如果是字符串或其他，转成字符串
                ac_str = str(ac_raw)
            # ----------------------------------------------------

            # 处理其他字段容错
            feat_name = actual_data.get('feature_name') or actual_data.get('title') or '未命名'
            if feat_name == '未命名' and actual_data.get('description'):
                feat_name = actual_data['description'][:15]

            src_content = actual_data.get('source_content') or actual_data.get('source_snippet') or ''

            params = (
                actual_data.get('project_id'),
                actual_data.get('module_name', '通用'),
                feat_name,
                actual_data.get('description', ''),
                ac_str,  # 🔥 使用处理后的字符串，而不是原始 List
                actual_data.get('requirement_type', '功能需求'),
                actual_data.get('priority', 'P1'),
                actual_data.get('confidence_score', 0.8),  # 默认 0.8 防止为空
                'Pending',
                actual_data.get('review_comments', ''),
                src_content
            )
            new_id = self.execute_insert(sql, params)
            return f"ID: {new_id}"
        except Exception as e:
            print(f"❌ Save Error: {e}")
            return f"Error: {str(e)}"
    
    def get_breakdown_page(self, page=1, size=10, project_id=None, feature_name=None, status=None):
        """
        分页查询 (供前端 ProTable 使用)
        """
        with self.get_connection() as conn:
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
            return result
    
    def update_breakdown_item(self, item_id: int, data: Dict[str, Any]):
        """
        更新功能点 (人工编辑用)
        """
        try:
            # 只允许更新部分核心字段
            sql = """
                UPDATE requirement_breakdown 
                SET module_name=?, feature_name=?, description=?, acceptance_criteria=?, priority=?, source_content=?, review_status='Pending'
                WHERE id=?
            """
            params = (
                data['module_name'],
                data['feature_name'],
                data['description'],
                data['acceptance_criteria'],
                data['priority'],
                data.get('source_content', ''),  # 🔥 增加参数绑定
                item_id
            )
            self.execute_update(sql, params)
            return True
        except Exception as e:
            print(f"Update Error: {e}")
            return False
    
    def update_breakdown_status(self, item_id: int, new_status: str):
        """更新状态，如果状态为 Pass，则同步到 functional_points"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
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

            return True
        except Exception as e:
            print(f"❌ Status Update Error: {e}")
            return False
    
    def get_batch_breakdown_items(self, ids: List[int]) -> List[Dict]:
        """
        批量获取需求拆解项 (用于 BreakdownList 页面批量生成)
        """
        return self.batch_query("requirement_breakdown", ids)
    
    def get_batch_functional_points(self, ids: List[int]) -> List[Dict]:
        """
        批量获取正式功能点 (用于 RequirementList 页面批量生成)
        """
        return self.batch_query("functional_points", ids)


# 实例化
requirement_db = RequirementDB()


# 保持向后兼容
def get_requirements_page(page=1, size=10, feature_name=None, priority=None):
    return requirement_db.get_requirements_page(page, size, feature_name, priority)

def get_requirement_by_id(req_id: int):
    return requirement_db.get_requirement_by_id(req_id)

def save_analyzed_point(data: Dict[str, Any]) -> str:
    return requirement_db.save_analyzed_point(data)

def save_breakdown_item(data: Dict[str, Any]) -> str:
    return requirement_db.save_breakdown_item(data)

def get_breakdown_page(page=1, size=10, project_id=None, feature_name=None, status=None):
    return requirement_db.get_breakdown_page(page, size, project_id, feature_name, status)

def update_breakdown_item(item_id: int, data: Dict[str, Any]):
    return requirement_db.update_breakdown_item(item_id, data)

def update_breakdown_status(item_id: int, new_status: str):
    return requirement_db.update_breakdown_status(item_id, new_status)

def get_batch_breakdown_items(ids: List[int]) -> List[Dict]:
    return requirement_db.get_batch_breakdown_items(ids)

def get_batch_functional_points(ids: List[int]) -> List[Dict]:
    return requirement_db.get_batch_functional_points(ids)
