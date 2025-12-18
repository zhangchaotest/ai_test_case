import sqlite3
import json
from typing import List, Dict, Annotated
import re

DB_PATH = "requirements.db"


def safe_json_loads(json_str):
    """辅助函数：尝试清洗并解析 JSON，处理 LLM 可能输出的 Markdown 格式"""
    if not json_str:
        return None

    # 1. 去除首尾空白
    cleaned = json_str.strip()

    # 2. 去除 Markdown 代码块标记 (```json ... ```)
    # 这一步非常关键，Gemini 经常喜欢加这个
    if cleaned.startswith("```"):
        # 去掉第一行 (```json)
        parts = cleaned.split("\n", 1)
        if len(parts) > 1:
            cleaned = parts[1]
        # 去掉最后一行 (```)
        if cleaned.strip().endswith("```"):
            cleaned = cleaned.strip()[:-3]

    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"⚠️ JSON 解析失败: {e}\n原始内容: {json_str}")
        return None


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 需求表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS functional_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT, feature_name TEXT, description TEXT, priority TEXT
        )
    """)
    # 用例表 (含新字段)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_id INTEGER,
            case_title TEXT, pre_condition TEXT, steps TEXT, expected_result TEXT,
            priority TEXT DEFAULT 'P1', case_type TEXT DEFAULT 'Functional',
            test_data TEXT, status TEXT DEFAULT 'Active', version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# 插入模拟数据 (方便你测试)
def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM functional_points")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO functional_points (module_name, feature_name, description, priority) VALUES (?, ?, ?, ?)",
                       ("登录模块", "用户密码登录", "用户输入正确的用户名和密码应能成功登录，密码错误应提示。支持最大长度限制。", "P0"))
        conn.commit()
    conn.close()

# --- CRUD 操作 ---

def get_requirements_list():
    """获取需求列表，并统计关联的用例数量"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = """
        SELECT fp.*, (SELECT COUNT(*) FROM test_cases tc WHERE tc.requirement_id = fp.id) as case_count 
        FROM functional_points fp ORDER BY fp.id DESC
    """
    cursor.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_requirement_by_id(req_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functional_points WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_test_cases_by_req_id(req_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_cases WHERE requirement_id = ?", (req_id,))

    rows = []
    for row in cursor.fetchall():
        # 将 row 转为字典
        d = dict(row)

        # --- 🔥 修复核心：健壮的 JSON 解析 ---
        steps_obj = safe_json_loads(d.get('steps'))
        # 如果解析失败或为空，给一个默认空列表，防止前端崩坏
        d['steps'] = steps_obj if isinstance(steps_obj, list) else []

        test_data_obj = safe_json_loads(d.get('test_data'))
        d['test_data'] = test_data_obj if isinstance(test_data_obj, dict) else {}

        # --- 🔥 修复核心：防止字段缺失导致 Pydantic 报错 ---
        # 如果是旧数据，可能没有 priority 字段，手动给默认值
        if 'priority' not in d or not d['priority']:
            d['priority'] = 'P1'
        if 'case_type' not in d or not d['case_type']:
            d['case_type'] = 'Functional'
        if 'status' not in d:
            d['status'] = 'Active'

        rows.append(d)

    conn.close()
    return rows

# ... 这里保留你之前的 save_verified_test_case 函数 ...
# 记得把 save_verified_test_case 中的 conn 路径改成 DB_PATH

def save_verified_test_case(
    requirement_id: int,
    case_title: Annotated[str, "用例标题"],
    pre_condition: Annotated[str, "前置条件"],
    steps: Annotated[List[Dict], "JSON格式的步骤"],
    expected_result: Annotated[str, "预期结果"],
    # 🔥 新增参数
    priority: Annotated[str, "优先级 (P0-P3)"],
    case_type: Annotated[str, "用例类型 (Functional/Negative/Boundary)"],
    test_data: Annotated[Dict, "测试数据键值对，如 {'user': 'admin'}"] = {}
) -> str:
    """
    [给评审Agent用] 将评审通过的测试用例保存到数据库。
    """
    try:
        # 1. 将列表转换为 JSON 字符串存库
        # ensure_ascii=False 保证存进去的是中文，不是 \uXXXX
        steps_json = json.dumps(steps, ensure_ascii=False)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO test_cases
                   (requirement_id, case_title, pre_condition, steps, expected_result,priority,case_type,test_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (requirement_id, case_title, pre_condition, steps_json, expected_result,priority,case_type,test_data)
        )
        conn.commit()
        cid = cursor.lastrowid
        conn.close()
        return f"✅ 用例已入库 (ID: {cid})"
    except Exception as e:
        return f"❌ 入库失败: {e}"