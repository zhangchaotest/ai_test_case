import sqlite3
import os

DB_FILE = "test_case.db"

def init_db():
    """初始化数据库并创建所需的数据表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 功能点表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    # 测试用例表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id INTEGER,
            title TEXT NOT NULL,
            steps TEXT,
            expected TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (feature_id) REFERENCES features (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn