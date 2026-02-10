import time
import redis
import json
import logging
import os
from typing import Optional
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RedisConnectionLimiter(BaseHTTPMiddleware):
    """
    基于Redis的分布式连接池限流中间件

    适用于8个worker环境的并发控制：
    - 每个worker最多15个并发
    - 总并发限制120个请求
    - 为160个数据库连接留40个余量
    """

    def __init__(
        self,
        app,
        redis_url: str = "redis://localhost:6379",
        max_concurrent_per_worker: int = 15,
        global_concurrent_limit: int = 120,
        key_prefix: str = "ai_chat_rate_limit",
        ttl: int = 120  # 请求超时时间，2分钟
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.max_concurrent_per_worker = max_concurrent_per_worker
        self.global_concurrent_limit = global_concurrent_limit
        self.key_prefix = key_prefix
        self.ttl = ttl
        self.worker_id = f"worker_{os.getpid()}"

        # 初始化Redis连接
        self._init_redis()

    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            logging.info(f"✅ Redis连接成功 - Worker ID: {self.worker_id}")
        except Exception as e:
            logging.error(f"❌ Redis连接失败: {e}")
            # 如果Redis不可用，回退到本地计数
            self.redis_client = None
            self._fallback_stats = {
                "current_concurrent": 0,
                "worker_concurrent": 0
            }

    def _get_worker_key(self) -> str:
        """获取当前worker的Redis key"""
        return f"{self.key_prefix}:worker:{self.worker_id}"

    def _get_global_key(self) -> str:
        """获取全局Redis key"""
        return f"{self.key_prefix}:global"

    def _increment_redis_counter(self) -> bool:
        """使用Redis增加并发计数"""
        if not self.redis_client:
            return self._fallback_increment()

        try:
            # 使用Redis管道提高性能
            with self.redis_client.pipeline() as pipe:
                worker_key = self._get_worker_key()
                global_key = self._get_global_key()

                # 监视并发限制
                pipe.watch(worker_key, global_key)

                # 获取当前计数
                worker_count = int(pipe.get(worker_key) or 0)
                global_count = int(pipe.get(global_key) or 0)

                # 检查限制
                if worker_count >= self.max_concurrent_per_worker:
                    pipe.unwatch()
                    return False

                if global_count >= self.global_concurrent_limit:
                    pipe.unwatch()
                    return False

                # 开始事务
                pipe.multi()

                # 增加计数
                pipe.incr(worker_key)
                pipe.expire(worker_key, self.ttl)

                pipe.incr(global_key)
                pipe.expire(global_key, self.ttl)

                # 执行事务
                pipe.execute()

                logging.debug(
                    f"并发计数增加 - Worker: {self.worker_id}, "
                    f"Worker并发: {worker_count + 1}, "
                    f"全局并发: {global_count + 1}"
                )

                return True

        except redis.WatchError:
            logging.warning("Redis并发冲突，重试中...")
            return False
        except Exception as e:
            logging.error(f"Redis操作失败: {e}")
            return self._fallback_increment()

    def _decrement_redis_counter(self):
        """使用Redis减少并发计数"""
        if not self.redis_client:
            return self._fallback_decrement()

        try:
            worker_key = self._get_worker_key()
            global_key = self._get_global_key()

            # 原子性减少计数
            with self.redis_client.pipeline() as pipe:
                pipe.decr(worker_key)
                pipe.decr(global_key)
                pipe.execute()

            logging.debug(f"并发计数减少 - Worker: {self.worker_id}")

        except Exception as e:
            logging.error(f"Redis减少计数失败: {e}")
            self._fallback_decrement()

    def _fallback_increment(self) -> bool:
        """Redis不可用时的本地fallback方案"""
        if self._fallback_stats["worker_concurrent"] >= self.max_concurrent_per_worker:
            return False
        if self._fallback_stats["current_concurrent"] >= self.global_concurrent_limit:
            return False

        self._fallback_stats["worker_concurrent"] += 1
        self._fallback_stats["current_concurrent"] += 1
        return True

    def _fallback_decrement(self):
        """Redis fallback的减少计数"""
        if self._fallback_stats["worker_concurrent"] > 0:
            self._fallback_stats["worker_concurrent"] -= 1
        if self._fallback_stats["current_concurrent"] > 0:
            self._fallback_stats["current_concurrent"] -= 1

    async def dispatch(self, request: Request, call_next):
        # 只对chat接口进行限流
        if "/chat/completions" not in request.url.path:
            return await call_next(request)

        # 尝试获取并发许可
        if not self._increment_redis_counter():
            stats = self._get_current_stats()

            logging.warning(
                f"分布式限流触发 - Worker: {self.worker_id}, "
                f"当前并发: {stats['total_concurrent']}, "
                f"Worker并发: {stats['worker_concurrent']}"
            )

            raise HTTPException(
                status_code=503,
                detail={
                    "error": "服务繁忙",
                    "message": "当前请求量过大，请稍后再试",
                    "retry_after": 5,
                    "stats": stats
                }
            )

        try:
            response = await call_next(request)
            return response
        finally:
            # 无论如何都要释放并发许可
            self._decrement_redis_counter()

    def _get_current_stats(self) -> dict:
        """获取当前统计信息"""
        if self.redis_client:
            try:
                worker_key = self._get_worker_key()
                global_key = self._get_global_key()

                worker_count = int(self.redis_client.get(worker_key) or 0)
                global_count = int(self.redis_client.get(global_key) or 0)

                return {
                    "worker_concurrent": worker_count,
                    "total_concurrent": global_count,
                    "max_per_worker": self.max_concurrent_per_worker,
                    "global_limit": self.global_concurrent_limit,
                    "worker_id": self.worker_id
                }
            except Exception as e:
                logging.error(f"获取Redis统计失败: {e}")

        # 返回fallback统计
        return {
            "worker_concurrent": self._fallback_stats["worker_concurrent"],
            "total_concurrent": self._fallback_stats["current_concurrent"],
            "max_per_worker": self.max_concurrent_per_worker,
            "global_limit": self.global_concurrent_limit,
            "worker_id": self.worker_id,
            "mode": "fallback"
        }