from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse  # 🔥 必须引入这个，进行流式输出
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from pydantic import BaseModel

from database import db_tools
from agents import agent_manager


from database import requirement_db, case_db

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


@app.get("/requirements")
def list_requirements(page: int = 1, size: int = 10, feature: str = None):
    """
    分页获取需求列表
    """
    return requirement_db.get_requirements_page(page, size, feature_name=feature)

@app.get("/requirements/{req_id}/generate_stream")
async def generate_cases_stream(req_id: int, count: int = 5, mode: str = "new"):
    """
    流式生成接口
    """
    req = db_tools.get_requirement_by_id(req_id)
    if not req:
        raise HTTPException(status_code=404, detail="未找到对应的需求")

    # 返回流式响应，media_type 必须是 text/event-stream
    return StreamingResponse(
        agent_manager.run_stream_task(
            req_id, req['feature_name'],
            req['description'],
            target_count=count,
            mode=mode
        ),
        media_type="text/event-stream"
    )

@app.get("/cases")  # 🔥 修改返回模型
def list_cases(page: int = 1, size: int = 10, req_id: int = None, status: str = None):

    return case_db.get_cases_page(page, size, req_id=req_id, status=status)

class BatchStatusRequest(BaseModel):
    ids: List[int]
    status: str


# 2. 新增批量评审接口
@app.put("/cases/batch_status")
def update_case_status(req: BatchStatusRequest):
    """批量更新用例状态 (评审通过/废弃)"""
    success = case_db.batch_update_status(req.ids, req.status)
    if success:
        return {"status": "success", "message": "操作成功"}
    raise HTTPException(status_code=500, detail="更新数据库失败")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
