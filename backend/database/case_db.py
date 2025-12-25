#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：case_db.py
@Author  ：张超
@Date    ：2025/12/21 12:50
@Desc    ：
"""
import re
from typing import Dict, Any, List

from .base import get_conn, execute_page_query, safe_json_loads
import json


def get_cases_page(page=1, size=10, req_id=None, title=None,status=None):
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if req_id:
        where_clauses.append("requirement_id = ?")
        params.append(req_id)

    if title:
        where_clauses.append("case_title LIKE ?")
        params.append(f"%{title}%")

    if status: # 🔥 新增 status 过滤逻辑
        where_clauses.append("status = ?")
        params.append(status)

    where_str = " AND ".join(where_clauses)

    base_sql = f"SELECT * FROM test_cases WHERE {where_str} ORDER BY id DESC"
    count_sql = f"SELECT COUNT(*) FROM test_cases WHERE {where_str}"

    # 1. 执行分页查询
    result = execute_page_query(cursor, base_sql, count_sql, tuple(params), page, size)

    # 2. [特有逻辑] 处理 JSON 字段 (steps, test_data)
    for item in result['items']:
        item['steps'] = safe_json_loads(item.get('steps')) or []
        item['test_data'] = safe_json_loads(item.get('test_data')) or {}

    conn.close()
    return result


# =============================================================================
# 1. 私有辅助函数：数据清洗与标准化
# =============================================================================

def _normalize_steps(steps_raw: Any) -> List[Dict]:
    """
    [辅助方法] 标准化测试步骤
    将各种奇葩格式 (字符串、数字、不规范列表) 统一清洗为标准 List[Dict]
    """
    print(f"\n🔍 [Data Clean] 原始 steps 类型: {type(steps_raw)}")

    # 情况 A: 已经是 List -> 直接返回
    if isinstance(steps_raw, list):
        return steps_raw

    # 情况 B: 是字符串 -> 尝试解析 JSON 或 清洗文本
    if isinstance(steps_raw, str):
        try:
            # 尝试直接解析 JSON
            parsed = json.loads(steps_raw)
            if isinstance(parsed, list):
                return parsed
        except:
            pass

        # 解析失败，进入文本清洗逻辑
        print(f"⚠️ [Data Fix] 检测到纯文本步骤，执行清洗...")
        cleaned_text = steps_raw.replace('\\n', '\n')
        lines = cleaned_text.strip().split('\n')

        fixed_steps = []
        for line in lines:
            line = line.strip()
            if not line: continue
            # 正则去除行首序号: "1. ", "1、", "(1)"
            clean_action = re.sub(r'^(\d+[.、\s)]?|\(\d+\))\s*', '', line)
            if clean_action:
                fixed_steps.append({
                    "step_id": len(fixed_steps) + 1,
                    "action": clean_action,
                    "expected": "（详见预期结果字段）"
                })

        # 兜底：如果清洗后为空，把原文本作为一条步骤
        return fixed_steps if fixed_steps else [{"step_id": 1, "action": steps_raw, "expected": "非标准格式"}]

    # 情况 C: 数字类型 -> 转换为占位符
    if isinstance(steps_raw, (int, float)):
        print(f"⚠️ [Data Fix1] 检测到数字类型: {steps_raw}")
        if steps_raw > 0:
            return [{"step_id": 1, "action": f"步骤 {steps_raw}", "expected": "AI未生成详细描述"}]
        return []

    # 情况 D: 其他 -> 返回空列表
    return []


def _normalize_test_data(test_data_raw: Any) -> Dict:
    """
    [辅助方法] 标准化测试数据
    统一转换为 Dict
    """
    if isinstance(test_data_raw, dict):
        return test_data_raw

    if isinstance(test_data_raw, str):
        try:
            return json.loads(test_data_raw)
        except:
            return {"raw_content": test_data_raw}

    print(f"⚠️ [Data Fix2] 检测到数字类型: {test_data_raw}")
    return {}


# =============================================================================
# 2. 主业务函数：数据库操作
# =============================================================================

def save_case(data: Dict[str, Any]) -> str:
    """
    保存单条用例
    职责：序列化标准对象 -> 执行 SQL 插入
    """
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if 'data' in data and isinstance(data['data'], dict):
            print("⚠️ [DB Fix] 检测到参数嵌套，正在解包...")
            data = data['data']

        req_id = data.get('requirement_id')
        if not req_id:
            print(f"❌ [DB Error] 缺少必填参数 'requirement_id'。当前数据: {data.keys()}")
            return "-1"  # 或者抛出异常让 Agent 重试
        # --- 1. 数据预处理 (调用辅助方法) ---
        # 无论输入多乱，这里出来的都是标准的 Python List 和 Dict
        final_steps_list = _normalize_steps(data.get('steps', []))
        final_test_data_dict = _normalize_test_data(data.get('test_data', {}))

        # --- 2. 序列化 (Python Object -> JSON String) ---
        # 统一在入库前做一次 dumps，避免双重序列化
        steps_json_str = json.dumps(final_steps_list, ensure_ascii=False)
        test_data_json_str = json.dumps(final_test_data_dict, ensure_ascii=False)

        print(f"💾 [DB Save] 最终存入 Steps: {steps_json_str}")
        print(f"💾 [DB Save] 最终存入 data: {data}")
        # --- 3. 准备 SQL 参数 ---
        sql = """
              INSERT INTO test_cases (requirement_id, case_title, pre_condition, steps, expected_result, \
                                      priority, case_type, test_data, status, \
                                      quality_score, review_comments) \
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              """

        params = (
            data['requirement_id'],
            data.get('case_title', '未命名用例'),
            data.get('pre_condition', '无'),
            steps_json_str,  # 存 JSON 字符串
            data.get('expected_result', '无'),
            data.get('priority', 'P1'),
            data.get('case_type', 'Functional'),
            test_data_json_str,  # 存 JSON 字符串
            'Draft',
            data.get('quality_score', 0.8),
            data.get('review_comments', '')
        )

        # --- 4. 执行事务 ---
        cursor.execute(sql, params)
        conn.commit()
        new_id = cursor.lastrowid

        print(f"✅ [DB Success] 用例保存成功 ID: {new_id}")
        return f"ID: {new_id}"

    except Exception as e:
        print(f"❌ [DB Error] 保存用例失败: {str(e)}")
        # 打印一下出错时的原始数据，方便排查
        # print(f"   -> Problem Data: {data}")
        return "-1"

    finally:
        if conn:
            conn.close()

def get_existing_case_titles(req_id: int):
    """获取指定需求下所有已存在的用例标题"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT case_title FROM test_cases WHERE requirement_id = ?", (req_id,))
    rows = cursor.fetchall()
    conn.close()
    # 返回列表: ['登录成功', '密码错误', ...]
    return [row['case_title'] for row in rows]

def batch_update_status(case_ids: List[int], new_status: str):
    """批量更新用例状态"""
    if not case_ids:
        return False

    conn = get_conn()
    cursor = conn.cursor()
    try:
        # 动态生成 SQL: UPDATE test_cases SET status = ? WHERE id IN (?,?,?)
        placeholders = ','.join(['?'] * len(case_ids))
        sql = f"UPDATE test_cases SET status = ? WHERE id IN ({placeholders})"

        # 参数列表: [status, id1, id2, id3...]
        params = [new_status] + case_ids

        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 批量更新失败: {e}")
        return False
    finally:
        conn.close()