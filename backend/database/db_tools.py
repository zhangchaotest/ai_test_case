import sqlite3
import json
from typing import List, Dict, Annotated
import re

DB_PATH = "requirements.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 需求表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS functional_points
                   (
                       id           INTEGER PRIMARY KEY AUTOINCREMENT,
                       module_name  TEXT,
                       feature_name TEXT,
                       description  TEXT,
                       priority     TEXT
                   )
                   """)
    # 用例表 (含新字段)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS test_cases
                   (
                       id              INTEGER PRIMARY KEY AUTOINCREMENT,
                       requirement_id  INTEGER,
                       case_title      TEXT,
                       pre_condition   TEXT,
                       steps           TEXT,
                       expected_result TEXT,
                       priority        TEXT      DEFAULT 'P1',
                       case_type       TEXT      DEFAULT 'Functional',
                       test_data       TEXT,
                       status          TEXT      DEFAULT 'Active',
                       version         INTEGER   DEFAULT 1,
                       created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)
    conn.commit()
    conn.close()
