#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：api.py
@Author  ：张超
@Date    ：2025/12/18 14:11
@Desc    ：
"""
# backend/api.py
import json
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入之前的逻辑
from db_tools import init_db
from autogen_agentchat.ui import Console
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from my_agents import create_requirement_analyst, create_test_generator, create_test_reviewer

# 初始化数据库
init_db()

app = FastAPI(title="AutoGen Test Platform")

# 允许跨域 (前端 5173 -> 后端 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic 模型 (用于数据验证) ---

class RequirementRequest(BaseModel):
    raw_text: str


class FunctionalPoint(BaseModel):
    id: int
    module_name: str
    feature_name: str
    description: str
    priority: str


class TestCase(BaseModel):
    id: int
    requirement_id: int
    case_title: str
    pre_condition: str
    steps: List[Dict[str, Any]]  # 接收 JSON Array
    expected_result: str
    priority: str
    case_type: str
    test_data: Optional[Dict[str, Any]] = {}
    status: str
    version: int


# --- 业务逻辑封装 ---

async def run_requirement_analysis(text: str):
    """运行需求分析 Agent"""
    agent = create_requirement_analyst()
    # 这里的 run_stream 会触发工具调用保存数据库
    await Console(agent.run_stream(task=text))


async def run_test_generation(req_id: int, feature_name: str, desc: str):
    """运行测试用例生成 Agent Team"""
    generator = create_test_generator()
    reviewer = create_test_reviewer()
    termination = TextMentionTermination("TERMINATE")

    team = RoundRobinGroupChat(
        participants=[generator, reviewer],
        termination_condition=termination,
        max_turns=10
    )

    task_desc = f"""
    【任务】为以下功能编写测试用例并存库。
    ID: {req_id}
    名称: {feature_name}
    描述: {desc}
    """
    await Console(team.run_stream(task=task_desc))


# --- API 接口 ---

@app.get("/requirements", response_model=List[FunctionalPoint])
def get_requirements():
    import sqlite3
    conn = sqlite3.connect("requirements.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functional_points ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


@app.post("/requirements/analyze")
async def analyze_requirement(request: RequirementRequest, background_tasks: BackgroundTasks):
    """
    提交需求分析任务。
    由于 AutoGen 运行较慢，建议使用 background_tasks 后台运行，
    或者直接 await 等待结果（演示使用 await 方便前端看 loading）。
    """
    try:
        await run_requirement_analysis(request.raw_text)
        return {"status": "success", "message": "分析完成，功能点已存入数据库"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-cases", response_model=List[TestCase])
def get_test_cases(req_id: Optional[int] = None):
    import sqlite3
    conn = sqlite3.connect("requirements.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = "SELECT * FROM test_cases"
    params = []
    if req_id:
        sql += " WHERE requirement_id = ?"
        params.append(req_id)

    sql += " ORDER BY id DESC"
    cursor.execute(sql, tuple(params))

    # 关键处理：将 SQLite 里的 JSON 字符串转回 Python 对象
    raw_rows = cursor.fetchall()
    results = []
    for row in raw_rows:
        d = dict(row)
        try:
            d['steps'] = json.loads(d['steps']) if d['steps'] else []
            d['test_data'] = json.loads(d['test_data']) if d['test_data'] else {}
        except:
            d['steps'] = []
            d['test_data'] = {}
        results.append(d)

    conn.close()
    return results


@app.post("/test-cases/generate/{req_id}")
async def generate_cases(req_id: int):
    # 1. 先查出需求详情
    import sqlite3
    conn = sqlite3.connect("requirements.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functional_points WHERE id = ?", (req_id,))
    req = cursor.fetchone()
    conn.close()

    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 2. 运行 Agent 生成
    try:
        await run_test_generation(req['id'], req['feature_name'], req['description'])
        return {"status": "success", "message": "测试用例生成完毕"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # 启动命令: python api.py
    uvicorn.run(app, host="0.0.0.0", port=8000)