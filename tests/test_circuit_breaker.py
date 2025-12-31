"""
断路器单元测试
"""
import pytest
import time
from unittest.mock import Mock, patch
from app.utils.circuit_breaker import DatabaseCircuitBreaker, CircuitState


class TestDatabaseCircuitBreaker:
    """数据库断路器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.breaker = DatabaseCircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,
            expected_exception=Exception
        )

    def test_breaker_initialization(self):
        """测试断路器初始化"""
        assert self.breaker.failure_threshold == 3
        assert self.breaker.recovery_timeout == 1.0
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0
        assert self.breaker.last_failure_time is None

    def test_should_attempt_reset_with_none_time(self):
        """测试last_failure_time为None时的重置检查"""
        self.breaker.last_failure_time = None
        assert self.breaker._should_attempt_reset() is False

    def test_should_attempt_reset_with_insufficient_time(self):
        """测试失败时间不足时的重置检查"""
        self.breaker.last_failure_time = time.time() - 0.5  # 0.5秒前失败
        assert self.breaker._should_attempt_reset() is False

    def test_should_attempt_reset_with_sufficient_time(self):
        """测试失败时间足够时的重置检查"""
        self.breaker.last_failure_time = time.time() - 2.0  # 2秒前失败
        assert self.breaker._should_attempt_reset() is True

    def test_successful_call_in_closed_state(self):
        """测试关闭状态下的成功调用"""
        @self.breaker
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
        assert self.breaker.state == CircuitState.CLOSED

    def test_failure_calls_below_threshold(self):
        """测试失败次数未达到阈值"""
        @self.breaker
        def failing_func():
            raise Exception("Test error")

        # 失败2次（小于阈值3）
        for _ in range(2):
            with pytest.raises(Exception):
                failing_func()

        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 2

    def test_failure_calls_reach_threshold(self):
        """测试失败次数达到阈值"""
        @self.breaker
        def failing_func():
            raise Exception("Test error")

        # 失败3次（达到阈值）
        for _ in range(3):
            with pytest.raises(Exception):
                failing_func()

        assert self.breaker.state == CircuitState.OPEN
        assert self.breaker.failure_count == 3
        assert self.breaker.last_failure_time is not None

    def test_open_state_blocks_calls(self):
        """测试开启状态阻止调用"""
        # 手动设置为开启状态
        self.breaker.state = CircuitState.OPEN
        self.breaker.last_failure_time = time.time()

        @self.breaker
        def test_func():
            return "success"

        with pytest.raises(Exception) as exc_info:
            test_func()

        assert "服务熔断" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 503

    def test_half_open_state_transition(self):
        """测试半开状态转换"""
        # 设置为开启状态，并让恢复时间过去
        self.breaker.state = CircuitState.OPEN
        self.breaker.last_failure_time = time.time() - 2.0  # 2秒前失败

        @self.breaker
        def test_func():
            return "success"

        # 第一次调用应该触发半开状态
        result = test_func()
        assert result == "success"
        assert self.breaker.state == CircuitState.HALF_OPEN

    def test_half_open_success_recovery(self):
        """测试半开状态下的成功恢复"""
        self.breaker.state = CircuitState.HALF_OPEN
        self.breaker.half_open_max_calls = 2

        @self.breaker
        def test_func():
            return "success"

        # 成功调用2次
        for _ in range(2):
            test_func()

        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0

    def test_half_open_failure_returns_to_open(self):
        """测试半开状态下失败返回开启状态"""
        self.breaker.state = CircuitState.HALF_OPEN

        @self.breaker
        def failing_func():
            raise Exception("Test error")

        with pytest.raises(Exception):
            failing_func()

        assert self.breaker.state == CircuitState.OPEN

    def test_reset_functionality(self):
        """测试重置功能"""
        # 设置失败状态
        self.breaker.state = CircuitState.OPEN
        self.breaker.failure_count = 3
        self.breaker.half_open_calls = 2
        self.breaker.last_failure_time = time.time()

        # 调用重置
        self.breaker._reset()

        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0
        assert self.breaker.half_open_calls == 0
        assert self.breaker.last_failure_time is None

    @patch('time.time')
    def test_retry_after_calculation(self, mock_time):
        """测试重试时间计算"""
        mock_time.return_value = 100.0
        self.breaker.recovery_timeout = 60.0
        self.breaker.last_failure_time = 80.0  # 20秒前失败

        @self.breaker
        def test_func():
            return "success"

        # 设置为开启状态
        self.breaker.state = CircuitState.OPEN

        with pytest.raises(Exception) as exc_info:
            test_func()

        # 验证重试时间计算 (60 - (100 - 80) = 40)
        retry_after = exc_info.value.detail.get("retry_after")
        assert retry_after == 40

    def test_database_connection_error_handling(self):
        """测试数据库连接错误处理"""
        @self.breaker
        def db_func():
            raise Exception("database connection timeout")

        with pytest.raises(Exception) as exc_info:
            db_func()

        # 验证返回的是HTTPException而不是原始异常
        assert "数据库连接失败" in str(exc_info.value.detail)

    def test_non_database_error_passthrough(self):
        """测试非数据库错误直接传递"""
        @self.breaker
        def other_func():
            raise ValueError("some other error")

        with pytest.raises(ValueError):
            other_func()

    def test_timeout_error_handling(self):
        """测试超时错误处理"""
        @self.breaker
        def timeout_func():
            raise Exception("connection timeout error")

        with pytest.raises(Exception) as exc_info:
            timeout_func()

        assert "数据库连接失败" in str(exc_info.value.detail)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])