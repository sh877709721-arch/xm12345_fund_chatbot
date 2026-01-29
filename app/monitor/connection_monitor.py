import logging
import time
import threading
from typing import Dict, Any
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool
from app.config.database import engine

class ConnectionPoolMonitor:
    """连接池监控器"""

    def __init__(self, engine: Engine, check_interval: float = 10.0):
        self.engine = engine
        self.check_interval = check_interval
        self.monitor_thread = None
        self.stop_monitoring = False
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "overflow_connections": 0,
            "checkout_failures": 0,
            "last_update": 0
        }

    def start_monitoring(self):
        """启动连接池监控"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.stop_monitoring = False
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logging.info("连接池监控已启动")

    def stop(self):
        """停止监控"""
        self.stop_monitoring = True
        if self.monitor_thread:
            self.monitor_thread.join()
        logging.info("连接池监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while not self.stop_monitoring:
            try:
                self._collect_stats()
                self._log_stats()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"连接池监控错误: {e}")
                time.sleep(5)

    def _get_pool_stats(self) -> Dict[str, int]:
        """安全地获取连接池统计信息，避免类型检查问题"""
        pool = self.engine.pool

        # 使用getattr来安全访问可能不存在类型注解的方法
        return {
            "size": getattr(pool, 'size', lambda: 0)(),
            "overflow": getattr(pool, 'overflow', lambda: 0)(),
            "checkedout": getattr(pool, 'checkedout', lambda: 0)(),
            "checkedin": getattr(pool, 'checkedin', lambda: 0)(),
            "checkout_failures": getattr(pool, 'checkout_failures', 0)
        }

    def _collect_stats(self):
        """收集连接池统计信息"""
        pool_stats = self._get_pool_stats()
        new_stats = {
            "total_connections": pool_stats["size"] + pool_stats["overflow"],
            "active_connections": pool_stats["checkedout"],
            "idle_connections": pool_stats["checkedin"],
            "overflow_connections": pool_stats["overflow"],
            "checkout_failures": pool_stats["checkout_failures"],
            "last_update": time.time()
        }
        self.stats.update(new_stats)

    def _log_stats(self):
        """记录连接池统计信息"""
        stats = self.stats
        total = stats["total_connections"]
        active = stats["active_connections"]
        idle = stats["idle_connections"]
        overflow = stats["overflow_connections"]

        # 计算使用率
        pool_size = self.engine.pool.size()
        usage_rate = (active / total * 100) if total > 0 else 0

        log_message = (
            f"连接池状态 - 总连接: {total}, "
            f"活跃: {active}, 空闲: {idle}, "
            f"溢出: {overflow}, 使用率: {usage_rate:.1f}%"
        )

        # 根据使用率选择日志级别
        if usage_rate > 90:
            logging.error(f"⚠️ 连接池高负载! {log_message}")
        elif usage_rate > 75:
            logging.warning(f"⚠️ 连接池中高负载: {log_message}")
        else:
            logging.info(f"✅ 连接池正常: {log_message}")

    def get_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        self._collect_stats()
        return self.stats.copy()

    def is_healthy(self) -> bool:
        """检查连接池是否健康"""
        self._collect_stats()
        total = self.stats["total_connections"]
        active = self.stats["active_connections"]

        # 如果连接数接近上限，认为不健康
        if total >= 150:  # 接近160的上限
            return False

        # 如果活跃连接占比过高，认为不健康
        if active / total > 0.9 if total > 0 else False:
            return False

        return True

# 全局连接池监控器实例
connection_monitor = ConnectionPoolMonitor(engine)

# 添加连接池事件监听器
def setup_connection_listeners():
    """设置连接池事件监听器"""

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logging.debug("新的数据库连接已建立")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        pool = engine.pool
        checkedout = getattr(pool, 'checkedout', lambda: 0)()
        size = getattr(pool, 'size', lambda: 0)()
        max_overflow = getattr(pool, 'max_overflow', lambda: 0)()

        if checkedout >= size + max_overflow - 5:
            logging.warning(f"连接池接近上限! 当前活跃: {checkedout}/{size + max_overflow}")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        logging.debug("数据库连接已归还到连接池")

    @event.listens_for(engine, "close")
    def receive_close(dbapi_connection, connection_record):
        logging.debug("数据库连接已关闭")