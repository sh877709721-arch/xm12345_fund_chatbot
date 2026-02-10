"""
机器人模块

包含所有机器人类型和工厂类的统一管理
"""

from .factory import AgentFactory, agent_factory
from .definitions import get_llm_config

# 导出主要接口
__all__ = [
    'AgentFactory',     # 机器人工厂类
    'agent_factory',    # 全局工厂实例
    'get_llm_config',   # 获取 LLM 配置
]