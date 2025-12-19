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


# backend/db_tools.py

def get_test_cases(req_id: int = None, title: str = None):
    """通用查询用例函数：支持按 req_id 筛选，或者查全部"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM test_cases WHERE 1=1"
    params = []

    if req_id:
        sql += " AND requirement_id = ?"
        params.append(req_id)

    if title:
        sql += " AND case_title LIKE ?"
        params.append(f"%{title}%")

    sql += " ORDER BY id DESC"  # 倒序排列，新的在前面

    cursor.execute(sql, tuple(params))

    rows = []
    for row in cursor.fetchall():
        d = dict(row)
        # 复用之前的安全解析逻辑
        d['steps'] = safe_json_loads(d.get('steps')) or []
        d['test_data'] = safe_json_loads(d.get('test_data')) or {}

        # 补全默认字段防止报错
        d.setdefault('priority', 'P1')
        d.setdefault('case_type', 'Functional')
        d.setdefault('status', 'Active')

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
    print(f"⚡️ [DEBUG] 正在尝试保存用例: {case_title}") # <--- 加这行

    try:
        # 1. 将列表转换为 JSON 字符串存库
        # ensure_ascii=False 保证存进去的是中文，不是 \uXXXX
        steps_json = json.dumps(steps, ensure_ascii=False)

        # 🔥🔥🔥 2. 修复点：处理 test_data (新增)
        # 必须把字典转成字符串，SQLite 才能存
        test_data_json = json.dumps(test_data, ensure_ascii=False) if test_data else "{}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO test_cases
               (requirement_id, case_title, pre_condition, steps, expected_result,
                priority, case_type, test_data, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                requirement_id,
                case_title,
                pre_condition,
                steps_json,  # 存字符串
                expected_result,
                priority,
                case_type,
                test_data_json,  # 🔥 存字符串 (原本这里传了 dict 导致报错)
                "Active"
            )
        )
        conn.commit()
        cid = cursor.lastrowid
        conn.close()
        print(f"✅ [DEBUG] 保存成功 ID: {cursor.lastrowid}") # <--- 加这行
        return f"✅ 用例已入库 (ID: {cid})"

    except Exception as e:
        print(f"❌ [DEBUG] 数据库保存报错: {str(e)}")      # <--- 加这行！！
        return f"❌ 入库失败: {e}"