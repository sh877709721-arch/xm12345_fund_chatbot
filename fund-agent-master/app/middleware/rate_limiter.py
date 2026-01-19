import time
import asyncio
from typing import Dict, Optional
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from threading import Lock

class ConnectionPoolLimiter(BaseHTTPMiddleware):
    """
    数据库连接池限流中间件

    基于当前活跃请求数进行限制，防止数据库连接耗尽
    """

    def __init__(self, app, max_concurrent_requests: int = 120, check_interval: float = 1.0):
        super().__init__(app)
        self.max_concurrent_requests = max_concurrent_requests  # 最大并发请求，留有余量
        self.active_requests: Dict[str, float] = {}  # 记录活跃请求的开始时间
        self.lock = Lock()
        self.last_cleanup = time.time()
        self.check_interval = check_interval

    async def dispatch(self, request: Request, call_next):
        # 只对chat接口进行限流
        if "/chat/completions" not in request.url.path:
            return await call_next(request)

        request_id = f"{id(request)}_{time.time()}"

        with self.lock:
            # 定期清理超时请求
            current_time = time.time()
            if current_time - self.last_cleanup > self.check_interval:
                self._cleanup_expired_requests(current_time)
                self.last_cleanup = current_time

            # 检查是否超过最大并发限制
            if len(self.active_requests) >= self.max_concurrent_requests:
                active_count = len(self.active_requests)
                logging.warning(f"连接池限流触发: 当前活跃请求 {active_count}, 最大限制 {self.max_concurrent_requests}")

                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "服务繁忙",
                        "message": "当前请求量过大，请稍后再试",
                        "retry_after": 5,
                        "active_requests": active_count,
                        "max_limit": self.max_concurrent_requests
                    }
                )

            # 记录新请求
            self.active_requests[request_id] = current_time

        try:
            response = await call_next(request)
            return response
        finally:
            # 无论如何都要清理请求记录
            with self.lock:
                self.active_requests.pop(request_id, None)

    def _cleanup_expired_requests(self, current_time: float):
        """清理超时的请求记录（防止内存泄漏）"""
        timeout = 120  # 2分钟超时
        expired_requests = [
            req_id for req_id, start_time in self.active_requests.items()
            if current_time - start_time > timeout
        ]

        for req_id in expired_requests:
            del self.active_requests[req_id]

        if expired_requests:
            logging.info(f"清理了 {len(expired_requests)} 个超时请求记录")


class RequestQueueLimiter(BaseHTTPMiddleware):
    """
    请求队列限流器 - 当连接池满时提供排队机制
    """

    def __init__(self, app, max_queue_size: int = 50, queue_timeout: float = 30.0):
        super().__init__(app)
        self.max_queue_size = max_queue_size
        self.queue_timeout = queue_timeout
        self.request_queue = asyncio.Queue(maxsize=max_queue_size)
        self.semaphore = asyncio.Semaphore(120)  # 对应连接池限制

    async def dispatch(self, request: Request, call_next):
        # 只对chat接口进行排队处理
        if "/chat/completions" not in request.url.path:
            return await call_next(request)

        # 尝试获取信号量，如果失败则进入队列
        if self.semaphore.locked():
            try:
                # 等待队列中有空位，超时则返回503
                await asyncio.wait_for(
                    self.request_queue.put(None),
                    timeout=self.queue_timeout
                )

                # 获得队列位置，现在等待信号量
                async with self.semaphore:
                    # 释放队列位置
                    try:
                        self.request_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass

                    return await call_next(request)

            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "队列超时",
                        "message": f"等待时间超过{self.queue_timeout}秒，请稍后再试",
                        "queue_size": self.request_queue.qsize(),
                        "max_queue_size": self.max_queue_size
                    }
                )
        else:
            async with self.semaphore:
                return await call_next(request)