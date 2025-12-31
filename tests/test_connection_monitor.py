"""
连接池监控器单元测试
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from app.monitor.connection_monitor import ConnectionPoolMonitor
from sqlalchemy.engine import Engine


class TestConnectionPoolMonitor:
    """连接池监控器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建模拟的引擎和连接池
        self.mock_engine = Mock(spec=Engine)
        self.mock_pool = Mock()
        self.mock_engine.pool = self.mock_pool

        # 创建监控器实例
        self.monitor = ConnectionPoolMonitor(self.mock_engine, check_interval=0.1)

    def test_monitor_initialization(self):
        """测试监控器初始化"""
        assert self.monitor.engine == self.mock_engine
        assert self.monitor.check_interval == 0.1
        assert self.monitor.stop_monitoring is False
        assert self.monitor.monitor_thread is None

        # 检查初始统计状态
        assert self.monitor.stats["total_connections"] == 0
        assert self.monitor.stats["active_connections"] == 0
        assert self.monitor.stats["idle_connections"] == 0

    def test_get_pool_stats(self):
        """测试连接池统计信息获取"""
        # 设置模拟方法的返回值
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 5
        self.mock_pool.checkedout.return_value = 7
        self.mock_pool.checkedin.return_value = 8
        self.mock_pool.checkout_failures = 2

        # 获取统计信息
        stats = self.monitor._get_pool_stats()

        # 验证返回值
        assert stats["size"] == 10
        assert stats["overflow"] == 5
        assert stats["checkedout"] == 7
        assert stats["checkedin"] == 8
        assert stats["checkout_failures"] == 2

        # 验证方法调用
        self.mock_pool.size.assert_called_once()
        self.mock_pool.overflow.assert_called_once()
        self.mock_pool.checkedout.assert_called_once()
        self.mock_pool.checkedin.assert_called_once()

    def test_get_pool_stats_fallback(self):
        """测试连接池方法不存在时的回退机制"""
        # 移除某个方法
        del self.mock_pool.checkedout
        del self.mock_pool.size
        del self.mock_pool.overflow

        # 获取统计信息
        stats = self.monitor._get_pool_stats()

        # 验证回退值
        assert stats["checkedout"] == 0
        assert stats["size"] == 0  # 因为方法被删除
        assert stats["overflow"] == 0  # 因为方法被删除

    def test_collect_stats(self):
        """测试统计信息收集"""
        # 设置模拟值
        self.mock_pool.size.return_value = 15
        self.mock_pool.overflow.return_value = 3
        self.mock_pool.checkedout.return_value = 12
        self.mock_pool.checkedin.return_value = 6
        self.mock_pool.checkout_failures = 1

        # 收集统计信息
        self.monitor._collect_stats()

        # 验证统计结果
        assert self.monitor.stats["total_connections"] == 18  # 15 + 3
        assert self.monitor.stats["active_connections"] == 12
        assert self.monitor.stats["idle_connections"] == 6
        assert self.monitor.stats["overflow_connections"] == 3
        assert self.monitor.stats["checkout_failures"] == 1
        assert self.monitor.stats["last_update"] > 0

    def test_get_stats_returns_copy(self):
        """测试get_stats返回的是副本而不是引用"""
        # 设置初始统计
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 5
        self.mock_pool.checkedin.return_value = 5
        self.monitor._collect_stats()

        # 获取统计副本
        stats = self.monitor.get_stats()

        # 修改返回的统计信息
        stats["total_connections"] = 999

        # 验证原始统计未受影响
        assert self.monitor.stats["total_connections"] != 999

    def test_is_healthy_true(self):
        """测试健康检查 - 正常情况"""
        # 设置健康的统计值
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 2
        self.mock_pool.checkedout.return_value = 8  # 使用率 8/12 = 67%
        self.monitor._collect_stats()

        # 验证健康状态
        assert self.monitor.is_healthy() is True

    def test_is_healthy_false_high_connections(self):
        """测试健康检查 - 连接数过高"""
        # 设置过高的连接数（超过150的阈值）
        self.mock_pool.size.return_value = 100
        self.mock_pool.overflow.return_value = 60
        self.mock_pool.checkedout.return_value = 50
        self.monitor._collect_stats()

        # 验证健康状态
        assert self.monitor.is_healthy() is False

    def test_is_healthy_false_high_usage_rate(self):
        """测试健康检查 - 使用率过高"""
        # 设置高使用率
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 10  # 使用率 100%
        self.monitor._collect_stats()

        # 验证健康状态
        assert self.monitor.is_healthy() is False

    def test_is_healthy_edge_case_zero_total(self):
        """测试健康检查 - 总连接数为0的边界情况"""
        # 设置0连接
        self.mock_pool.size.return_value = 0
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 0
        self.monitor._collect_stats()

        # 验证健康状态
        assert self.monitor.is_healthy() is True

    @patch('time.sleep')
    def test_monitor_loop_normal_operation(self, mock_sleep):
        """测试监控循环正常运行"""
        # 设置模拟值
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 5
        self.mock_pool.checkedin.return_value = 5

        # 设置停止标志，让循环只运行一次
        def stop_after_first_call(seconds):
            self.monitor.stop_monitoring = True

        mock_sleep.side_effect = stop_after_first_call

        # 运行监控循环
        self.monitor._monitor_loop()

        # 验证统计信息被收集
        assert self.monitor.stats["total_connections"] == 10
        assert self.monitor.stats["active_connections"] == 5

    @patch('logging.error')
    @patch('time.sleep')
    def test_monitor_loop_handles_exceptions(self, mock_sleep, mock_log_error):
        """测试监控循环处理异常"""
        # 设置池方法抛出异常
        self.mock_pool.size.side_effect = Exception("连接池错误")

        # 设置停止标志
        def stop_after_first_call(seconds):
            self.monitor.stop_monitoring = True

        mock_sleep.side_effect = stop_after_first_call

        # 运行监控循环
        self.monitor._monitor_loop()

        # 验证异常被记录
        mock_log_error.assert_called()
        call_args = mock_log_error.call_args[0][0]
        assert "连接池监控错误" in call_args

    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        # 测试启动监控
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            self.monitor.start_monitoring()

            # 验证线程被创建和启动
            mock_thread.assert_called_once_with(target=self.monitor._monitor_loop, daemon=True)
            mock_thread_instance.start.assert_called_once()

        # 测试停止监控
        self.monitor.stop_monitoring = True
        with patch.object(self.monitor.monitor_thread, 'join') as mock_join:
            self.monitor.stop()
            mock_join.assert_called_once()

    def test_start_monitoring_already_running(self):
        """测试启动已经运行的监控"""
        # 创建一个已经运行的线程
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        self.monitor.monitor_thread = mock_thread

        # 尝试启动
        with patch('threading.Thread') as mock_thread_class:
            self.monitor.start_monitoring()

            # 验证没有创建新线程
            mock_thread_class.assert_not_called()

    @patch('logging.info')
    def test_log_stats_normal_usage(self, mock_log_info):
        """测试正常使用率的日志记录"""
        # 设置正常使用率 (70%)
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 7
        self.monitor._collect_stats()

        # 记录日志
        self.monitor._log_stats()

        # 验证info级别日志被调用
        mock_log_info.assert_called()
        call_args = mock_log_info.call_args[0][0]
        assert "连接池正常" in call_args

    @patch('logging.warning')
    def test_log_stats_high_usage(self, mock_log_warning):
        """测试高使用率的日志记录"""
        # 设置高使用率 (80%)
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 8
        self.monitor._collect_stats()

        # 记录日志
        self.monitor._log_stats()

        # 验证warning级别日志被调用
        mock_log_warning.assert_called()
        call_args = mock_log_warning.call_args[0][0]
        assert "连接池中高负载" in call_args

    @patch('logging.error')
    def test_log_stats_critical_usage(self, mock_log_error):
        """测试极高使用率的日志记录"""
        # 设置极高使用率 (95%)
        self.mock_pool.size.return_value = 10
        self.mock_pool.overflow.return_value = 0
        self.mock_pool.checkedout.return_value = 10  # 100% 使用率 > 90%
        self.mock_pool.checkedin.return_value = 0
        self.monitor._collect_stats()

        # 记录日志
        self.monitor._log_stats()

        # 验证error级别日志被调用
        mock_log_error.assert_called()
        call_args = mock_log_error.call_args[0][0]
        assert "连接池高负载" in call_args


class TestConnectionListeners:
    """连接池事件监听器测试类"""

    @patch('app.monitor.connection_monitor.engine')
    @patch('app.monitor.connection_monitor.event')
    def test_connection_listeners_setup(self, mock_event, mock_engine):
        """测试连接监听器设置"""
        # 这里主要测试监听器设置函数是否可以被调用
        # 实际的监听器功能需要真实的数据库连接才能测试
        from app.monitor.connection_monitor import setup_connection_listeners

        # 调用设置函数，不应该抛出异常
        try:
            setup_connection_listeners()
            setup_success = True
        except Exception as e:
            setup_success = False
            print(f"Exception occurred: {e}")

        assert setup_success is True

        # 验证事件监听器被注册
        mock_event.listens_for.assert_called()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])