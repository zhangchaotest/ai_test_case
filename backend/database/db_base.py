#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
数据库基础操作类
封装了常用的数据库 CRUD 操作，提供统一的接口供上层业务调用。
"""

import sqlite3
from typing import List, Dict, Any

from .base import get_conn


class DatabaseBase:
    """
    数据库操作基类
    提供连接获取、插入、更新、查询等通用方法
    """
    
    def get_connection(self):
        """
        获取数据库连接
        :return: sqlite3.Connection 对象
        """
        return get_conn()
    
    def execute_insert(self, sql: str, params: tuple = None) -> int:
        """
        执行插入操作
        
        :param sql: SQL 插入语句
        :param params: SQL 参数元组，防止 SQL 注入
        :return: 新插入记录的 ID (lastrowid)
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
        执行更新或删除操作
        
        :param sql: SQL 更新/删除语句
        :param params: SQL 参数元组
        :return: 受影响的行数 (rowcount)
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
        
        :param sql: SQL 查询语句
        :param params: SQL 参数元组
        :return: 查询结果列表，每条记录为一个字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
            # 将 sqlite3.Row 对象转换为字典
            return [dict(row) for row in rows]
    
    def get_by_id(self, table: str, id_value: int) -> Dict[str, Any]:
        """
        根据主键 ID 获取单条记录
        
        :param table: 表名
        :param id_value: 主键 ID 值
        :return: 记录字典，如果不存在则返回 None
        """
        sql = f"SELECT * FROM {table} WHERE id = ?"
        rows = self.execute_query(sql, (id_value,))
        return rows[0] if rows else None
    
    def batch_query(self, table: str, ids: List[int]) -> List[Dict[str, Any]]:
        """
        批量根据 ID 获取多条记录
        
        :param table: 表名
        :param ids: ID 列表
        :return: 记录列表
        """
        if not ids:
            return []
        # 生成占位符字符串，如 "?,?,?"
        placeholders = ','.join(['?'] * len(ids))
        sql = f"SELECT * FROM {table} WHERE id IN ({placeholders})"
        return self.execute_query(sql, tuple(ids))
    
    def batch_update(self, table: str, ids: List[int], field: str, value: Any) -> bool:
        """
        批量更新多条记录的同一个字段
        
        :param table: 表名
        :param ids: ID 列表
        :param field: 要更新的字段名
        :param value: 新的字段值
        :return: 是否更新成功 (至少有一行受影响)
        """
        if not ids:
            return False
        placeholders = ','.join(['?'] * len(ids))
        sql = f"UPDATE {table} SET {field} = ? WHERE id IN ({placeholders})"
        # 参数顺序：新值, ID1, ID2, ...
        params = (value,) + tuple(ids)
        try:
            rows_affected = self.execute_update(sql, params)
            return rows_affected > 0
        except Exception as e:
            print(f"Error in batch_update: {e}")
            return False
