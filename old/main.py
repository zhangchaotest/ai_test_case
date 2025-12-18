import sqlite3
import os
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from database import init_db
from agents import user_proxy, analyst_agent, qa_agent
from models import TextInput, IdList, GenerateInput

# 加载环境变量
load_dotenv()

# 初始化数据库
init_db()

# FastAPI 应用
app = FastAPI()

# 添加 CORS 中间件以允许前端请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默认端口
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 分析需求 ---
def _run_analyze(text: str):
    user_proxy.initiate_chat(
        analyst_agent,
        message=f"需求文档内容:\n{text}"
    )

@app.post("/api/analyze")
async def analyze_req(input: TextInput, tasks: BackgroundTasks):
    # 在开始前清除旧的待处理数据，用于演示目的
    conn = sqlite3.connect("test_case.db")
    conn.execute("DELETE FROM features WHERE status='pending'")
    conn.commit()
    conn.close()

    tasks.add_task(_run_analyze, input.text)
    return {"msg": "分析已开始"}

# --- 2. 获取/确认功能点 ---
@app.get("/api/features/pending")
def get_pending_features():
    conn = sqlite3.connect("test_case.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM features WHERE status='pending'")
    rows = [{"id": r[0], "name": r[1], "description": r[2]} for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/features/confirm")
def confirm_features(input: IdList):
    conn = sqlite3.connect("test_case.db")
    placeholders = ','.join('?' for _ in input.ids)
    conn.execute(f"UPDATE features SET status='confirmed' WHERE id IN ({placeholders})", input.ids)
    conn.commit()
    conn.close()
    return {"msg": "功能点已确认"}

# --- 3. 生成测试用例 ---
def _run_generate(feature_ids: List[int]):
    conn = sqlite3.connect("test_case.db")
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in feature_ids)
    cursor.execute(f"SELECT id, name, description FROM features WHERE id IN ({placeholders})", feature_ids)
    features = cursor.fetchall()
    conn.close()

    # 构造提示词
    prompt = "请根据以下已确认的功能点生成测试用例:\n"
    for f in features:
        prompt += f"[功能点 ID: {f[0]}] 名称: {f[1]}, 描述: {f[2]}\n"

    user_proxy.initiate_chat(qa_agent, message=prompt)

@app.post("/api/generate")
async def generate_cases(input: GenerateInput, tasks: BackgroundTasks):
    conn = sqlite3.connect("test_case.db")
    conn.execute("DELETE FROM test_cases WHERE status='pending'")
    conn.commit()
    conn.close()

    tasks.add_task(_run_generate, input.feature_ids)
    return {"msg": "生成已开始"}

# --- 4. 获取/确认测试用例 ---
@app.get("/api/testcases/pending")
def get_pending_cases():
    conn = sqlite3.connect("test_case.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, feature_id, title, steps, expected FROM test_cases WHERE status='pending'")
    rows = [{"id": r[0], "feature_id": r[1], "title": r[2], "steps": r[3], "expected": r[4]} for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/testcases/confirm")
def confirm_cases(input: IdList):
    conn = sqlite3.connect("test_case.db")
    placeholders = ','.join('?' for _ in input.ids)
    conn.execute(f"UPDATE test_cases SET status='confirmed' WHERE id IN ({placeholders})", input.ids)
    conn.commit()
    conn.close()
    return {"msg": "测试用例已保存到数据库"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)