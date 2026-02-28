#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
提示词管理数据库操作模块
负责提示词 (Prompts) 的增删改查，支持按领域和类型筛选。
"""

from typing import Dict, Any, List

from .db_base import DatabaseBase


class PromptDB(DatabaseBase):
    """
    提示词数据库操作类
    继承自 DatabaseBase
    """
    
    def create_table(self):
        """
        创建提示词表
        (通常由 init_db.py 统一管理，此处保留作为独立初始化的备选方案)
        """
        sql = """
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            domain TEXT NOT NULL,
            type TEXT NOT NULL,  -- generator 或 reviewer
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
    
    def get_prompts(self, domain: str = None, type: str = None):
        """
        获取提示词列表
        支持多条件组合筛选
        
        :param domain: 领域 (如 base, web, api)
        :param type: 类型 (如 generator, reviewer)
        :return: 提示词列表 List[Dict]
        """
        sql = "SELECT * FROM prompts WHERE 1=1"
        params = []
        
        if domain:
            sql += " AND domain = ?"
            params.append(domain)
        
        if type:
            sql += " AND type = ?"
            params.append(type)
        
        sql += " ORDER BY id DESC"
        
        return self.execute_query(sql, tuple(params))
    
    def get_prompt_by_id(self, prompt_id: int):
        """
        根据 ID 获取单条提示词详情
        
        :param prompt_id: 提示词 ID
        :return: 提示词详情字典
        """
        sql = "SELECT * FROM prompts WHERE id = ?"
        rows = self.execute_query(sql, (prompt_id,))
        return rows[0] if rows else None
    
    def create_prompt(self, data: Dict[str, Any]):
        """
        创建新提示词
        
        :param data: 包含 name, content, domain, type, description 的字典
        :return: 新提示词 ID
        """
        sql = """
        INSERT INTO prompts (name, content, domain, type, description)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            data['name'],
            data['content'],
            data['domain'],
            data['type'],
            data.get('description', '')
        )
        return self.execute_insert(sql, params)
    
    def update_prompt(self, prompt_id: int, data: Dict[str, Any]):
        """
        更新提示词信息
        
        :param prompt_id: 要更新的提示词 ID
        :param data: 包含更新字段的字典
        :return: 是否更新成功 (True/False)
        """
        sql = """
        UPDATE prompts SET
            name = ?,
            content = ?,
            domain = ?,
            type = ?,
            description = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        params = (
            data['name'],
            data['content'],
            data['domain'],
            data['type'],
            data.get('description', ''),
            prompt_id
        )
        rows_affected = self.execute_update(sql, params)
        return rows_affected > 0
    
    def delete_prompt(self, prompt_id: int):
        """
        删除提示词
        
        :param prompt_id: 要删除的提示词 ID
        :return: 是否删除成功 (True/False)
        """
        sql = "DELETE FROM prompts WHERE id = ?"
        rows_affected = self.execute_update(sql, (prompt_id,))
        return rows_affected > 0


# 实例化全局对象
prompt_db = PromptDB()


# =========================================================
# 兼容性封装 (保持向后兼容，供旧代码调用)
# =========================================================
def init_prompt_table():
    """初始化提示词表"""
    prompt_db.create_table()

def get_prompts(domain: str = None, type: str = None):
    return prompt_db.get_prompts(domain, type)

def get_prompt_by_id(prompt_id: int):
    return prompt_db.get_prompt_by_id(prompt_id)

def create_prompt(data: Dict[str, Any]):
    return prompt_db.create_prompt(data)

def update_prompt(prompt_id: int, data: Dict[str, Any]):
    return prompt_db.update_prompt(prompt_id, data)

def delete_prompt(prompt_id: int):
    return prompt_db.delete_prompt(prompt_id)
