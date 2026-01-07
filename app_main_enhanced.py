from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.router import chat
from app.middleware.rate_limiter import ConnectionPoolLimiter
from app.monitor.connection_monitor import connection_monitor, setup_connection_listeners
from slowapi.errors import RateLimitExceeded
from app.middleware.api_rate_limiter import limiter, custom_rate_limit_handler
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("🚀 AI Chat Service 启动中...")

    # 启动连接池监控
    setup_connection_listeners()
    connection_monitor.start_monitoring()
    logger.info("✅ 连接池监控已启动")

    logger.info("📊 连接池保护已启用: 最大并发120，安全余量40")

    yield  # 应用运行期间

    # 关闭时执行
    logger.info("🛑 正在关闭 AI Chat Service...")
    connection_monitor.stop()
    logger.info("✅ 连接池监控已停止")

def create_app():
    app = FastAPI(
        title="AI Chat Service",
        description="优化的AI聊天服务，包含连接池保护机制",
        version="2.0.0",
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

    # 🔧 核心优化：连接池限流中间件
    app.add_middleware(
        ConnectionPoolLimiter,
        max_concurrent_requests=120,  # 最大并发120，留40连接余量
        check_interval=1.0            # 每秒检查一次
    )

    # 🚀 API 限流器注册
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    logger.info("✅ API 限流器已注册")

    # 注册路由
    app.include_router(chat.router, prefix="/api/v1")
    logger.info("✅ 路由已注册")

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """基础健康检查"""
        return {"status": "healthy", "service": "ai-chat"}

    @app.get("/health/database")
    async def database_health():
        """数据库连接池健康检查"""
        stats = connection_monitor.get_stats()
        is_healthy = connection_monitor.is_healthy()

        status_code = 200 if is_healthy else 503

        response_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "pool_stats": stats,
            "workers": 8,
            "max_connections": 160,
            "safety_margin": 40,  # 安全余量
            "utilization": f"{stats['active_connections'] / stats['total_connections'] * 100:.1f}%" if stats['total_connections'] > 0 else "0%"
        }

        if not is_healthy:
            response_data["alert"] = "连接池使用率过高，请关注系统负载"

        return response_data, status_code

    # 连接池状态监控端点
    @app.get("/monitor/pool")
    async def pool_status():
        """详细的连接池状态"""
        return connection_monitor.get_stats()

    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app_main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1  # 开发环境使用单worker
    )