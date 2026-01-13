
from fastapi import FastAPI, Request,Depends
from fastapi.responses import HTMLResponse
from typing import Union
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from app.router.chat import router as chat_router
from app.router.auth import router as auth_router
from app.router.admin import router as admin_router
from app.router.speech import router as speech_router
#from app.router.graphrag import router as graphrag_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from app.service.auth import get_current_user
from app.middleware.auth_logging import (
    AuthLoggingMiddleware,
    get_current_user_from_request,
    get_token_info_from_request,
    get_username_from_request,
    get_token_validity_from_request
)
from slowapi.errors import RateLimitExceeded
from app.middleware.api_rate_limiter import limiter, custom_rate_limit_handler
# 前端部署域名，生产环境请改为具体地址，例如 ["https://app.example.com"]
origins = ["http://127.0.0.1","http://127.0.0.1:8000","http://127.0.0.1:5173","http://localhost:5173"]
#origins = ["http://172.21.33.8","http://172.21.33.8:8000","http://172.21.33.8:8888"]


# -------------------- DB --------------------
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:   
    yield

app = FastAPI(lifespan=lifespan)    


# 添加认证日志中间件，用于记录用户认证信息
app.add_middleware(
    AuthLoggingMiddleware,
    exclude_paths=[
        "/health",
        "/debug-now",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
        "/assets/",
        "/znkfzs/assets/",
        "/workspace/",
        "/znkfzs/v1/chat/reset-chat-session",
        "/znkfzs/v1/auth/token",
        "/znkfzs/v1/auth/front_token",
        "/znkfzs/v1/chat/get_resent_messages",
        "/znkfzs/v1/chat/completions",
        "/znkfzs/v1/chat/get_similary_qa",
        "/znkfzs/v1/chat/get_reference_content",
        "/znkfzs/v1/feedback",
        "/znkfzs/v1/chat/intent",
        "/znkfzs/v1/speech",
        "/znkfzs/v1/admin/dashboard",
    ]
)

# 添加 CORS 中间件，解决跨域请求问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

app.include_router(chat_router, prefix="/znkfzs/v1", tags=["chat"])
app.include_router(admin_router, prefix="/znkfzs/v1", tags=["admin"])
app.include_router(auth_router, prefix="/znkfzs/v1", tags=["auth"]) #,dependencies=[Depends(get_current_user)]
app.include_router(speech_router, prefix="/znkfzs/v1", tags=["speech"])
#app.include_router(graphrag_router, prefix="/v1", tags=["graphrag"])

FRONTEND_DIR = Path(__file__).parent/"ui"
WORKSPACE_DIR = Path(__file__).parent/"workspace"
UPLOADS_DIR = Path(__file__).parent/"uploads"
@app.get("/health")
def read_root():
    return {"time": datetime.now(),"message":"OK"}

# 示例路由：展示如何使用中间件中的用户信息
@app.get("/user-profile")
async def user_profile(request: Request):
    """
    获取当前用户信息 - 使用中间件中的用户数据
    """
    current_user = get_current_user_from_request(request)

    if not current_user:
        return {
            "message": "未认证用户",
            "user": None,
            "timestamp": datetime.now()
        }

    # 从中间件获取token信息
    token_info = get_token_info_from_request(request)

    return {
        "message": "当前用户信息",
        "user": current_user,
        "token_info": token_info,
        "timestamp": datetime.now()
    }

# 示例路由：演示可选用户认证依赖
@app.get("/optional-auth")
async def optional_auth_route(request: Request):
    """
    可选认证路由 - 使用中间件解析的用户信息
    """
    current_user = get_current_user_from_request(request)
    username = get_username_from_request(request)

    if current_user:
        return {
            "message": f"欢迎回来，{username}!",
            "user": current_user,
            "authenticated": True
        }
    else:
        return {
            "message": "你好，访客！",
            "user": None,
            "authenticated": False
        }

# 示例路由：查看token有效期
@app.get("/token-status")
async def token_status_route(request: Request):
    """
    查看当前token状态和有效期
    """
    username = get_username_from_request(request)
    token_validity = get_token_validity_from_request(request)

    if not username:
        return {"message": "未提供token"}

    return {
        "username": username,
        "token_validity": token_validity,
        "timestamp": datetime.now()
    }

@app.get("/debug-now")
def debug_now():
    now = datetime.now()
    return {
        "str": now.strftime("%Y-%m-%d %H:%M:%S"),
        "repr": repr(now),
        "tzinfo": str(now.tzinfo)
    }

# 先挂载静态资源
app.mount("/znkfzs/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/workspace", StaticFiles(directory=WORKSPACE_DIR), name="workspace")
#app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
#app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="spa")

# 匹配workspace下的文件
@app.get("/workspace/{full_path:path}")
async def serve_workspace(full_path: str):
    file_path = WORKSPACE_DIR / full_path
    if file_path.exists():
        return FileResponse(file_path)
    return {"detail": "File not found"}, 404

# ✅ 兜底路由：所有未匹配到的路径都返回 index.html


@app.get("/znkfzs/{full_path:path}", response_class=HTMLResponse)
async def serve_znkfzs_spa(request: Request, full_path: str):
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return {"detail": "index.html not found"}, 404
    


@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(request: Request, full_path: str):
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return {"detail": "index.html not found"}, 404
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)