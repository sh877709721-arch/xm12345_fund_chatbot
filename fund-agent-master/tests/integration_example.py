# 在您的 main.py 中添加以下代码

from app.middleware.rate_limiter import ConnectionPoolLimiter
from app.monitor.connection_monitor import connection_monitor, setup_connection_listeners

def create_app():
    app = FastAPI(title="AI Chat Service")

    # 1. 添加连接池限流中间件（在其他中间件之前）
    app.add_middleware(
        ConnectionPoolLimiter,
        max_concurrent_requests=120,  # 留有40个连接余量
        check_interval=1.0
    )

    # 2. 启动连接池监控
    setup_connection_listeners()
    connection_monitor.start_monitoring()

    # 3. 注册路由（已有）
    app.include_router(chat.router)

    @app.on_event("shutdown")
    async def shutdown_event():
        connection_monitor.stop()

    return app

# 4. 添加连接池健康检查端点
@app.get("/health/database")
async def database_health():
    """数据库连接池健康检查"""
    from app.monitor.connection_monitor import connection_monitor

    stats = connection_monitor.get_stats()
    is_healthy = connection_monitor.is_healthy()

    status_code = 200 if is_healthy else 503

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "pool_stats": stats,
        "workers": 8,
        "max_connections": 160,
        "utilization": f"{stats['active_connections'] / stats['total_connections'] * 100:.1f}%" if stats['total_connections'] > 0 else "0%"
    }, status_code