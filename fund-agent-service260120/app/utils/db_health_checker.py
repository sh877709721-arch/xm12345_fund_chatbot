"""
数据库连接池健康检查工具
用于监控和管理数据库连接池状态
"""

import asyncio
import logging
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.config.database import engine, async_engine, db_monitor

logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """数据库健康检查器"""

    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        self.monitor = db_monitor

    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        try:
            pool = self.engine.pool
            async_pool = self.async_engine.pool

            sync_stats = {
                'sync_pool': {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid(),
                    'total_connections': pool.size() + pool.overflow(),
                }
            }

            async_stats = {
                'async_pool': {
                    'size': async_pool.size(),
                    'checked_in': async_pool.checkedin(),
                    'checked_out': async_pool.checkedout(),
                    'overflow': async_pool.overflow(),
                    'invalid': async_pool.invalid(),
                    'total_connections': async_pool.size() + async_pool.overflow(),
                }
            }

            return {**sync_stats, **async_stats}

        except Exception as e:
            logger.error(f"获取连接池统计信息失败: {e}")
            return {'error': str(e)}

    def check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接健康状态"""
        try:
            with self.engine.connect() as connection:
                # 执行简单查询测试连接
                result = connection.execute(text("SELECT 1 as health_check"))
                health_status = result.scalar() == 1

                return {
                    'status': 'healthy' if health_status else 'unhealthy',
                    'timestamp': asyncio.get_event_loop().time(),
                    'query_result': health_status
                }

        except SQLAlchemyError as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                'status': 'error',
                'timestamp': asyncio.get_event_loop().time(),
                'error': str(e)
            }

    async def check_async_database_connection(self) -> Dict[str, Any]:
        """检查异步数据库连接健康状态"""
        try:
            async with self.async_engine.connect() as connection:
                result = await connection.execute(text("SELECT 1 as health_check"))
                health_status = result.scalar() == 1

                return {
                    'status': 'healthy' if health_status else 'unhealthy',
                    'timestamp': asyncio.get_event_loop().time(),
                    'query_result': health_status
                }

        except SQLAlchemyError as e:
            logger.error(f"异步数据库健康检查失败: {e}")
            return {
                'status': 'error',
                'timestamp': asyncio.get_event_loop().time(),
                'error': str(e)
            }

    def get_connection_pool_recommendations(self) -> Dict[str, Any]:
        """获取连接池优化建议"""
        stats = self.get_connection_pool_stats()
        recommendations = []

        # 检查同步连接池
        if 'sync_pool' in stats:
            sync_pool = stats['sync_pool']

            # 检查连接池使用率
            if sync_pool['checked_out'] > sync_pool['size'] * 0.8:
                recommendations.append({
                    'type': 'sync_pool_size',
                    'message': '同步连接池使用率过高，建议增加pool_size',
                    'current_size': sync_pool['size'],
                    'suggested_size': min(sync_pool['size'] * 2, 100)
                })

            # 检查溢出连接
            if sync_pool['overflow'] > 0:
                recommendations.append({
                    'type': 'sync_overflow',
                    'message': '同步连接池存在溢出连接，建议增加pool_size或减少并发',
                    'current_overflow': sync_pool['overflow']
                })

        # 检查异步连接池
        if 'async_pool' in stats:
            async_pool = stats['async_pool']

            if async_pool['checked_out'] > async_pool['size'] * 0.8:
                recommendations.append({
                    'type': 'async_pool_size',
                    'message': '异步连接池使用率过高，建议增加pool_size',
                    'current_size': async_pool['size'],
                    'suggested_size': min(async_pool['size'] * 2, 100)
                })

        return {
            'recommendations': recommendations,
            'stats': stats
        }

    def log_health_status(self):
        """记录健康状态到日志"""
        stats = self.get_connection_pool_stats()
        health = self.check_database_connection()

        logger.info("=== 数据库连接池健康检查 ===")
        logger.info(f"连接池统计: {stats}")
        logger.info(f"数据库健康状态: {health}")

        recommendations = self.get_connection_pool_recommendations()
        if recommendations['recommendations']:
            logger.warning("优化建议:")
            for rec in recommendations['recommendations']:
                logger.warning(f"- {rec['message']}")

# 创建全局健康检查器实例
health_checker = DatabaseHealthChecker()

# 定期健康检查任务
async def periodic_health_check(interval: int = 300):
    """定期执行健康检查（默认5分钟）"""
    while True:
        try:
            health_checker.log_health_status()
            await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"定期健康检查失败: {e}")
            await asyncio.sleep(60)  # 出错时1分钟后重试

def start_health_monitoring():
    """启动健康监控（在应用启动时调用）"""
    # 在后台启动健康检查任务
    asyncio.create_task(periodic_health_check())
    logger.info("数据库连接池健康监控已启动")