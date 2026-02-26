# backend/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import traceback

# 引入 API 路由
from backend.api import api_router
# 引入数据库初始化
from backend.database import init_db


# 自定义错误响应模型
class ErrorResponse(BaseModel):
    status: str
    message: str
    detail: str = None


# =========================================================
# 1. 定义生命周期 (替代 on_event startup)
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 系统启动中：正在初始化数据库...")
    try:
        init_db.init_tables()
        init_db.seed_data()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise e
    yield
    print("🛑 系统关闭")


app = FastAPI(title="AI Test Platform", lifespan=lifespan)

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    # 记录异常信息
    print(f"❌ 全局异常: {exc}")
    print(traceback.format_exc())
    
    # 返回统一的错误响应
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "服务器内部错误",
            "detail": str(exc) if isinstance(exc, HTTPException) else "系统异常，请联系管理员"
        }
    )


# 注册 API 路由
app.include_router(api_router)


if __name__ == "__main__":
    # 建议使用 0.0.0.0 以便局域网访问，端口统一
    uvicorn.run(app, host="0.0.0.0", port=8888)
