from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models import db_tools
from agents import agent_manager
from backend.models import models

app = FastAPI(title="AI Test Platform")

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 初始化数据库
@app.on_event("startup")
def startup():
    db_tools.init_db()
    db_tools.seed_data()


@app.get("/requirements", response_model=List[models.Requirement])
def list_requirements():
    return db_tools.get_requirements_list()


@app.post("/requirements/{req_id}/generate")
async def generate_cases(req_id: int):
    """
    触发生成用例。因为耗时较长，这里直接 await 等待结果。
    前端需要展示 Loading 状态。
    """
    req = db_tools.get_requirement_by_id(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    print(req)
    try:
        # 调用 AutoGen 逻辑
        await agent_manager.run_generation_task(req_id, req['feature_name'], req['description'])
        return {"status": "success", "message": "Test cases generated and saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/requirements/{req_id}/cases", response_model=List[models.TestCaseResponse])
def get_cases(req_id: int):
    print(req_id)
    return db_tools.get_test_cases_by_req_id(req_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)