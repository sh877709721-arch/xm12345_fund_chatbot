import random
import asyncio
import logging
from typing import List, Dict, Optional, Any
import aiohttp
from app.config.settings import settings
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMLoadBalancer:
    """LLM服务器负载均衡器"""

    def __init__(self, servers: List[Dict[str, str]], strategy: str = "round_robin"):
        """
        初始化负载均衡器

        Args:
            servers: 服务器配置列表
            strategy: 负载均衡策略 (round_robin, random, least_loaded)
        """
        self.servers = servers
        self.strategy = strategy
        self.current_index = 0
        self.health_status = {server['url']: True for server in servers}
        self.server_loads = {server['url']: 0 for server in servers}  # 当前负载计数
        self.last_health_check = 0
        self.health_check_interval = 60  # 健康检查间隔(秒)

    async def health_check(self):
        """执行健康检查"""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return

        self.last_health_check = current_time
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            tasks = []
            for server in self.servers:
                tasks.append(self._check_server_health(session, server))

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"健康检查过程中发生错误: {e}")

    async def _check_server_health(self, session: aiohttp.ClientSession, server: Dict):
        """检查单个服务器健康状态"""
        try:
            headers = {}
            if server.get('api_key'):
                headers["Authorization"] = f"Bearer {server['api_key']}"

            async with session.get(
                f"{server['url']}/models",
                headers=headers
            ) as response:
                if response.status == 200:
                    if not self.health_status[server['url']]:
                        logger.info(f"服务器 {server['url']} 恢复正常")
                    self.health_status[server['url']] = True
                else:
                    logger.warning(f"服务器 {server['url']} 状态异常: HTTP {response.status}")
                    self.health_status[server['url']] = False
        except Exception as e:
            if self.health_status[server['url']]:
                logger.warning(f"服务器 {server['url']} 不可用: {str(e)}")
            self.health_status[server['url']] = False

    def get_available_servers(self) -> List[Dict]:
        """获取可用的服务器列表"""
        return [
            server for server in self.servers
            if self.health_status.get(server['url'], False)
        ]

    def get_next_server(self) -> Optional[Dict]:
        """根据策略获取下一个服务器"""
        available = self.get_available_servers()

        if not available:
            raise Exception("所有LLM服务器都不可用")

        if self.strategy == "round_robin":
            server = available[self.current_index % len(available)]
            self.current_index += 1
        elif self.strategy == "random":
            server = random.choice(available)
        elif self.strategy == "least_loaded":
            server = min(available, key=lambda x: self.server_loads.get(x['url'], 0))
        else:
            server = available[0]  # 默认使用第一个

        # 增加负载计数
        self.server_loads[server['url']] += 1
        logger.info(f"选择服务器: {server['url']} (当前负载: {self.server_loads[server['url']]})")

        return server

    def release_server(self, server_url: str):
        """释放服务器资源"""
        if server_url in self.server_loads and self.server_loads[server_url] > 0:
            self.server_loads[server_url] -= 1

    def get_server_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        return {
            "servers": [
                {
                    "url": server['url'],
                    "healthy": self.health_status.get(server['url'], False),
                    "current_load": self.server_loads.get(server['url'], 0)
                }
                for server in self.servers
            ],
            "strategy": self.strategy,
            "available_count": len(self.get_available_servers())
        }


def create_llm_config(server: Dict) -> Dict:
    """根据服务器信息创建LLM配置"""
    return {
        'model': server.get('model', 'Qwen3-32B'),
        'model_server': server['url'],
        'api_key': server.get('api_key', settings.OPENAI_API_KEY),
        'generate_cfg': {
            'temperature': server.get('temperature', 0.1),
            'top_p': server.get('top_p', 0.9),
            'extra_body': {
                'enable_thinking': server.get('enable_thinking', False)
            }
        }
    }


# 默认服务器配置
DEFAULT_SERVERS = [
    {
        'url': 'http://172.21.33.8/api/llm2/v1',
        'api_key': settings.OPENAI_API_KEY,
        'model': 'Qwen3-32B',
        'temperature': 0.1,
        'top_p': 0.9,
        'enable_thinking': False
    },
    # 添加更多服务器配置
    # {
    #     'url': 'http://172.21.33.9/api/llm2/v1',
    #     'api_key': settings.OPENAI_API_KEY,
    #     'model': 'Qwen3-32B',
    #     'temperature': 0.1,
    #     'top_p': 0.9,
    #     'enable_thinking': False
    # },
]

# 全局负载均衡器实例
_load_balancer: Optional[LLMLoadBalancer] = None

def get_load_balancer(servers: List[Dict] = None, strategy: str = "round_robin") -> LLMLoadBalancer:
    """获取负载均衡器实例"""
    global _load_balancer
    if _load_balancer is None or servers is not None:
        _load_balancer = LLMLoadBalancer(
            servers=servers or DEFAULT_SERVERS,
            strategy=strategy
        )
    return _load_balancer

async def get_current_llm_config(servers: List[Dict] = None) -> Dict:
    """获取当前的LLM配置（带负载均衡）"""
    load_balancer = get_load_balancer(servers)
    await load_balancer.health_check()
    server = load_balancer.get_next_server()
    return create_llm_config(server)