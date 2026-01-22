import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException

class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态

class DatabaseCircuitBreaker:
    """
    数据库连接熔断器

    当数据库连接错误率达到阈值时，暂时停止处理请求
    """

    def __init__(
        self,
        failure_threshold: int = 5,      # 失败阈值
        recovery_timeout: float = 60.0,  # 恢复超时时间（秒）
        expected_exception: type = Exception,
        half_open_max_calls: int = 3     # 半开状态最大调用次数
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logging.info("熔断器进入半开状态，尝试恢复")
                else:
                    # 计算剩余恢复时间（此时 last_failure_time 不为 None）
                    assert self.last_failure_time is not None, "熔断器状态为OPEN时，last_failure_time不应为None"
                    time_since_failure = time.time() - self.last_failure_time
                    retry_after = int(self.recovery_timeout - time_since_failure)
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": "服务熔断",
                            "message": "数据库服务暂时不可用，正在自动恢复",
                            "retry_after": retry_after
                        }
                    )

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result

            except self.expected_exception as e:
                self._on_failure()
                # 如果是数据库连接相关错误，重新抛出
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    logging.error(f"数据库连接错误: {e}")
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": "数据库连接失败",
                            "message": "数据库连接出现问题，请稍后再试"
                        }
                    )
                raise

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        if self.last_failure_time is None:
            return False

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout

    def _on_success(self):
        """成功时的处理"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self._reset()
                logging.info("熔断器恢复到正常状态")

    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logging.error("熔断器从半开状态回到熔断状态")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logging.error(f"熔断器触发，失败次数: {self.failure_count}")

    def _reset(self):
        """重置熔断器"""
        self.failure_count = 0
        self.half_open_calls = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

# 全局熔断器实例
database_circuit_breaker = DatabaseCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=Exception
)