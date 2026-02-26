#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
提示词管理数据库操作模块
"""

from typing import Dict, Any, List

from .db_base import DatabaseBase


class PromptDB(DatabaseBase):
    """提示词数据库操作类"""
    
    def create_table(self):
        """创建提示词表"""
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
        
        :param domain: 领域
        :param type: 类型
        :return: 提示词列表
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
        根据ID获取提示词
        
        :param prompt_id: 提示词ID
        :return: 提示词信息
        """
        sql = "SELECT * FROM prompts WHERE id = ?"
        rows = self.execute_query(sql, (prompt_id,))
        return rows[0] if rows else None
    
    def create_prompt(self, data: Dict[str, Any]):
        """
        创建提示词
        
        :param data: 提示词数据
        :return: 新创建的提示词ID
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
        更新提示词
        
        :param prompt_id: 提示词ID
        :param data: 提示词数据
        :return: 是否成功
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
        
        :param prompt_id: 提示词ID
        :return: 是否成功
        """
        sql = "DELETE FROM prompts WHERE id = ?"
        rows_affected = self.execute_update(sql, (prompt_id,))
        return rows_affected > 0


# 实例化
prompt_db = PromptDB()


# 初始化表结构
def init_prompt_table():
    """初始化提示词表"""
    prompt_db.create_table()


# 保持向后兼容
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
