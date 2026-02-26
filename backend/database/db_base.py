#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
数据库基础类
"""

import sqlite3
from typing import List, Dict, Any

from .base import get_conn


class DatabaseBase:
    """数据库操作基类"""
    
    def get_connection(self):
        """获取数据库连接"""
        return get_conn()
    
    def execute_insert(self, sql: str, params: tuple = None) -> int:
        """
        执行插入操作
        
        :param sql: SQL语句
        :param params: 参数
        :return: 新插入的ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor.lastrowid
    
    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行更新操作
        
        :param sql: SQL语句
        :param params: 参数
        :return: 影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor.rowcount
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询操作
        
        :param sql: SQL语句
        :param params: 参数
        :return: 查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_by_id(self, table: str, id_value: int) -> Dict[str, Any]:
        """
        根据ID获取记录
        
        :param table: 表名
        :param id_value: ID值
        :return: 记录字典
        """
        sql = f"SELECT * FROM {table} WHERE id = ?"
        rows = self.execute_query(sql, (id_value,))
        return rows[0] if rows else None
    
    def batch_query(self, table: str, ids: List[int]) -> List[Dict[str, Any]]:
        """
        批量根据ID获取记录
        
        :param table: 表名
        :param ids: ID列表
        :return: 记录列表
        """
        if not ids:
            return []
        placeholders = ','.join(['?'] * len(ids))
        sql = f"SELECT * FROM {table} WHERE id IN ({placeholders})"
        return self.execute_query(sql, tuple(ids))
