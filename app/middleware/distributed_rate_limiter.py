import time
import threading
import os
import mmap
import json
import logging
from typing import Dict, Optional
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class SharedMemoryCounter:
    """使用共享内存实现跨worker的计数器"""

    def __init__(self, max_concurrent: int = 15):
        self.max_concurrent = max_concurrent  # 每个worker最多15个并发
        self.worker_id = os.getpid()  # 使用进程ID作为worker标识
        self.shared_memory_path = "/tmp/ai_chat_shared_counter"

        # 创建或打开共享内存文件
        self._init_shared_memory()

    def _init_shared_memory(self):
        """初始化共享内存"""
        try:
            # 尝试打开现有的共享内存文件
            self.file = open(self.shared_memory_path, "r+b")
        except FileNotFoundError:
            # 创建新的共享内存文件
            self.file = open(self.shared_memory_path, "w+b")
            # 初始化数据结构
            initial_data = {
                "workers": {},  # 每个worker的并发数
                "last_cleanup": time.time()
            }
            self.file.write(json.dumps(initial_data).ljust(1024).encode())
            self.file.flush()

        # 创建内存映射
        self.mmap = mmap.mmap(self.file.fileno(), 1024)
        self.lock = threading.Lock()

    def _read_shared_data(self) -> Dict:
        """读取共享数据"""
        try:
            with self.lock:
                self.mmap.seek(0)
                data = self.mmap.read(1024).decode().strip('\x00')
                return json.loads(data)
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"读取共享数据失败: {e}")
            return {"workers": {}, "last_cleanup": time.time()}

    def _write_shared_data(self, data: Dict):
        """写入共享数据"""
        try:
            with self.lock:
                self.mmap.seek(0)
                json_data = json.dumps(data).ljust(1024)
                self.mmap.write(json_data.encode())
                self.mmap.flush()
        except OSError as e:
            logging.error(f"写入共享数据失败: {e}")

    def increment(self) -> bool:
        """增加并发计数，返回是否成功"""
        current_time = time.time()

        # 清理超时的worker记录
        self._cleanup_dead_workers(current_time)

        data = self._read_shared_data()

        # 检查当前worker的并发数
        current_count = data["workers"].get(str(self.worker_id), 0)

        # 单worker限制检查
        if current_count >= self.max_concurrent:
            return False

        # 总并发数检查
        total_concurrent = sum(data["workers"].values())
        if total_concurrent >= 120:  # 总并发限制120
            return False

        # 增加计数
        data["workers"][str(self.worker_id)] = current_count + 1
        self._write_shared_data(data)

        return True

    def decrement(self):
        """减少并发计数"""
        data = self._read_shared_data()
        worker_id_str = str(self.worker_id)

        if worker_id_str in data["workers"]:
            if data["workers"][worker_id_str] > 0:
                data["workers"][worker_id_str] -= 1

                # 如果计数为0，移除该worker记录
                if data["workers"][worker_id_str] == 0:
                    del data["workers"][worker_id_str]

                self._write_shared_data(data)

    def _cleanup_dead_workers(self, current_time: float):
        """清理已死亡的worker记录"""
        data = self._read_shared_data()

        # 每5分钟清理一次
        if current_time - data["last_cleanup"] < 300:
            return

        # 检查worker进程是否还存在
        dead_workers = []
        for worker_id_str in data["workers"].keys():
            try:
                worker_id = int(worker_id_str)
                # 尝试向进程发送信号0，检查进程是否存在
                os.kill(worker_id, 0)
            except (OSError, ValueError):
                dead_workers.append(worker_id_str)

        # 移除死亡worker的记录
        for worker_id_str in dead_workers:
            del data["workers"][worker_id_str]

        data["last_cleanup"] = current_time
        self._write_shared_data(data)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        data = self._read_shared_data()
        return {
            "total_concurrent": sum(data["workers"].values()),
            "active_workers": len(data["workers"]),
            "max_concurrent_per_worker": self.max_concurrent,
            "global_limit": 120,
            "workers_detail": data["workers"]
        }

class DistributedConnectionLimiter(BaseHTTPMiddleware):
    """
    分布式连接池限流中间件

    8个worker环境下的并发控制：
    - 每个worker最多15个并发请求
    - 总并发限制120个请求
    - 为数据库连接留40个余量
    """

    def __init__(self, app, max_concurrent_per_worker: int = 15):
        super().__init__(app)
        self.counter = SharedMemoryCounter(max_concurrent_per_worker)
        self.request_times: Dict[str, float] = {}
        self.lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        # 只对chat接口进行限流
        if "/chat/completions" not in request.url.path:
            return await call_next(request)

        request_id = f"{id(request)}_{time.time()}"

        # 尝试获取并发许可
        if not self.counter.increment():
            # 获取统计信息用于错误响应
            stats = self.counter.get_stats()

            logging.warning(
                f"分布式限流触发 - "
                f"Worker ID: {self.counter.worker_id}, "
                f"当前并发: {stats['total_concurrent']}, "
                f"活跃Worker: {stats['active_workers']}"
            )

            raise HTTPException(
                status_code=503,
                detail={
                    "error": "服务繁忙",
                    "message": "当前请求量过大，请稍后再试",
                    "retry_after": 5,
                    "current_concurrent": stats["total_concurrent"],
                    "max_concurrent": stats["global_limit"],
                    "active_workers": stats["active_workers"],
                    "worker_id": self.counter.worker_id
                }
            )

        try:
            response = await call_next(request)
            return response
        finally:
            # 无论如何都要释放并发许可
            self.counter.decrement()

    def get_limiter_stats(self) -> Dict:
        """获取限流器统计信息"""
        return self.counter.get_stats()