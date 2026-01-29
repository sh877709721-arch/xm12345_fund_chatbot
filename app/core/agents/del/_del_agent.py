# Copyright 2025 Mingtai Lin. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
机器人模块 - 向后兼容接口

保留原有的导入方式，同时重定向到新的 app.core.agents 包
"""

# 导入新的工厂和机器人实例
from app.core.agents import agent_factory

# 为了向后兼容，从工厂中获取机器人实例
bot = agent_factory.get_agent('bot')
rag_bot = agent_factory.get_agent('rag_bot')
qwen_rag_bot = agent_factory.get_agent('qwen_rag_bot')

# 也可以直接导入工厂类
from app.core.agents.factory import AgentFactory

# 向后兼容的导出
__all__ = [
    'bot',           # 公积金助手
    'rag_bot',       # 基础助手
    'guideline_bot',
    'qwen_rag_bot',  # RAG助手
    'AgentFactory',  # 工厂类
    'agent_factory'  # 全局工厂实例
]

# 添加废弃警告信息（可选）
import warnings

def _deprecation_warning():
    """发出废弃警告"""
    warnings.warn(
        "直接从 app.core.agent 导入机器人实例的方式已废弃。"
        "请使用新的统一入口: from app.core.agents import agent_factory",
        DeprecationWarning,
        stacklevel=3
    )

# 在用户直接导入这些变量时发出警告
class _DeprecationProxy:
    """废弃代理类，在访问时发出废弃警告"""

    def __init__(self, target_obj, name):
        self._target_obj = target_obj
        self._name = name

    def __getattr__(self, attr):
        _deprecation_warning()
        return getattr(self._target_obj, attr)

    def __call__(self, *args, **kwargs):
        _deprecation_warning()
        return self._target_obj(*args, **kwargs)

    def __repr__(self):
        _deprecation_warning()
        return repr(self._target_obj)

# 包装原有导出，提供废弃警告
bot = _DeprecationProxy(bot, 'bot')
rag_bot = _DeprecationProxy(rag_bot, 'rag_bot')
qwen_rag_bot = _DeprecationProxy(qwen_rag_bot, 'qwen_rag_bot')