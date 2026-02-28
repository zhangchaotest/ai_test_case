#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：requirement_db.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：需求数据库操作模块
负责需求功能点 (Functional Points) 和需求拆解项 (Requirement Breakdown) 的增删改查。
"""
import json
from typing import Dict, Any, List

from backend.database.base import execute_page_query
from backend.database.db_base import DatabaseBase


class RequirementDB(DatabaseBase):
    """
    需求数据库操作类
    继承自 DatabaseBase
    """
    
    def get_requirements_page(self, page=1, size=10, feature_name=None, priority=None):
        """
        分页获取功能点列表 (Functional Points)
        
        :param page: 当前页码
        :param size: 每页条数
        :param feature_name: 功能名称模糊查询
        :param priority: 优先级过滤
        :return: 分页结果字典
        """
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
            # 关联查询 test_cases 表，统计每个功能点下的用例数量
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
        """
        根据 ID 获取功能点详情
        
        :param req_id: 功能点 ID
        :return: 功能点详情字典
        """
        return self.get_by_id("functional_points", req_id)
    
    def save_analyzed_point(self, data: Dict[str, Any]) -> str:
        """
        保存分析出的功能点 (通常由 Agent 调用)
        将 AI 分析结果存入 functional_points 表
        
        :param data: 功能点数据
        :return: 新插入的 ID 或错误信息
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
        """
        保存需求拆解项 (Requirement Breakdown)
        这是 AI 分析后的中间态数据，用于人工评审
        
        :param data: 拆解项数据
        :return: 新插入的 ID 或错误信息
        """
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
        分页查询需求拆解项 (供前端 ProTable 使用)
        
        :param page: 当前页码
        :param size: 每页条数
        :param project_id: 项目ID过滤
        :param feature_name: 功能名称模糊查询
        :param status: 评审状态过滤
        :return: 分页结果字典
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
        更新需求拆解项 (人工编辑用)
        更新后状态会自动重置为 'Pending'，等待再次评审
        
        :param item_id: 拆解项 ID
        :param data: 更新数据
        :return: 是否成功
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
        """
        更新评审状态
        如果状态变为 'Pass'，则自动将该拆解项同步到 functional_points 表，作为正式功能点
        
        :param item_id: 拆解项 ID
        :param new_status: 新状态 (Pass/Reject/Discard)
        :return: 是否成功
        """
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
                        # 插入到 functional_points
                        # 注意：row 是 sqlite3.Row 或 tuple，取决于连接配置。这里假设是 tuple 或可通过索引访问
                        # 字段顺序需对应：project_id, module_name, feature_name, description, priority, source_content
                        # 假设 row 包含所有字段，我们需要按名称提取
                        # 为了稳健，建议使用 dict(row) 如果 row_factory 设置了的话
                        
                        # 这里简化处理，假设 row 顺序已知或使用 dict
                        item = dict(row)
                        
                        insert_sql = """
                            INSERT INTO functional_points 
                            (project_id, module_name, feature_name, description, priority, source_content)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """
                        cursor.execute(insert_sql, (
                            item['project_id'],
                            item['module_name'],
                            item['feature_name'],
                            item['description'],
                            item['priority'],
                            item['source_content']
                        ))
                        print(f"✅ [Sync] 拆解项 ID {item_id} 已同步至功能点库")
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Status Update Error: {e}")
            return False
    
    def get_batch_functional_points(self, req_ids: List[int]):
        """
        批量获取功能点
        
        :param req_ids: 功能点ID列表
        :return: 功能点列表
        """
        if not req_ids:
            return []
        
        placeholders = ','.join(['?'] * len(req_ids))
        sql = f"SELECT * FROM functional_points WHERE id IN ({placeholders})"
        rows = self.execute_query(sql, tuple(req_ids))
        return rows
    
    def get_batch_breakdown_items(self, item_ids: List[int]):
        """
        批量获取需求拆解项
        
        :param item_ids: 拆解项ID列表
        :return: 拆解项列表
        """
        if not item_ids:
            return []
        
        placeholders = ','.join(['?'] * len(item_ids))
        sql = f"SELECT * FROM requirement_breakdown WHERE id IN ({placeholders})"
        rows = self.execute_query(sql, tuple(item_ids))
        return rows

# 实例化并导出方法，供外部直接调用
requirement_db = RequirementDB()
get_batch_functional_points = requirement_db.get_batch_functional_points
get_batch_breakdown_items = requirement_db.get_batch_breakdown_items
save_breakdown_item = requirement_db.save_breakdown_item
get_requirements_page = requirement_db.get_requirements_page
get_requirement_by_id = requirement_db.get_requirement_by_id
save_analyzed_point = requirement_db.save_analyzed_point
get_breakdown_page = requirement_db.get_breakdown_page
update_breakdown_item = requirement_db.update_breakdown_item
update_breakdown_status = requirement_db.update_breakdown_status