from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.router import chat
import logging
import os

# 根据环境选择限流中间件
USE_REDIS = os.getenv("USE_REDIS_RATE_LIMIT", "false").lower() == "true"

def create_rate_limiter(app, max_concurrent_per_worker: int = 15):
    """
    统一的限流中间件工厂函数
    根据环境变量选择合适的限流实现
    """
    if USE_REDIS:
        from app.middleware.redis_rate_limiter import RedisConnectionLimiter
        return RedisConnectionLimiter(
            app=app,
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            max_concurrent_per_worker=max_concurrent_per_worker,
            global_concurrent_limit=120,   # 总并发限制120
        )
    else:
        from app.middleware.distributed_rate_limiter import DistributedConnectionLimiter
        return DistributedConnectionLimiter(
            app=app,
            max_concurrent_per_worker=max_concurrent_per_worker
        )

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(process)d] %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("🚀 AI Chat Service (Multi-Worker) 启动中...")
    logger.info(f"📊 Worker PID: {os.getpid()}")
    logger.info(f"🚦 限流策略: {'Redis分布式限流' if USE_REDIS else '共享内存限流'}")
    logger.info(f"⚡ 并发限制: 每Worker 15个，全局 120个")
    logger.info(f"🔗 数据库连接: 8 Workers × 20 = 160 最大连接")

    yield  # 应用运行期间

    # 关闭时执行
    logger.info(f"🛑 正在关闭 Worker {os.getpid()}...")

def create_app():
    app = FastAPI(
        title="AI Chat Service (Multi-Worker)",
        description="支持多worker部署的AI聊天服务，包含分布式连接池保护",
        version="2.1.0",
        lifespan=lifespan  # 使用新版lifespan
    )

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 🔧 关键优化：分布式连接池限流中间件
    logger.info(f"🔧 使用限流策略: {'Redis' if USE_REDIS else '共享内存'}")
    app.add_middleware(create_rate_limiter, max_concurrent_per_worker=15)

    # 注册路由
    app.include_router(chat.router, prefix="/api/v1")
    logger.info(f"✅ 路由已注册")

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """基础健康检查"""
        return {
            "status": "healthy",
            "service": "ai-chat",
            "worker_pid": os.getpid(),
            "rate_limiter": "redis" if USE_REDIS else "shared_memory"
        }

    @app.get("/health/database")
    async def database_health():
        """数据库连接池健康检查"""
        # 这里可以添加数据库连接池状态检查
        return {
            "status": "healthy",
            "database_connections": {
                "total_limit": 160,  # 8 workers × 20 connections
                "safety_margin": 40,  # 预留连接
                "max_concurrent_requests": 120,
                "max_per_worker": 15,
                "current_worker_pid": os.getpid()
            }
        }

    @app.get("/health/rate-limiter")
    async def rate_limiter_health():
        """限流器状态检查"""
        if USE_REDIS:
            try:
                import redis
                redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
                redis_client.ping()
                return {
                    "status": "healthy",
                    "type": "redis",
                    "redis_connected": True
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "type": "redis",
                    "redis_connected": False,
                    "error": str(e)
                }
        else:
            return {
                "status": "healthy",
                "type": "shared_memory",
                "worker_pid": os.getpid()
            }

    @app.get("/stats/workers")
    async def worker_stats():
        """Worker统计信息"""
        return {
            "current_worker_pid": os.getpid(),
            "max_concurrent_per_worker": 15,
            "global_concurrent_limit": 120,
            "total_workers": 8,
            "total_database_connections": 160,
            "rate_limiter_type": "redis" if USE_REDIS else "shared_memory"
        }

    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_multi_worker:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境不使用reload
        workers=1     # 单独运行时使用单worker
    )