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
机器人工厂类

统一的机器人实例管理和访问入口
"""

from typing import Dict, Union, Optional
from app.core.agents.react_chat import ReActChat
from app.core.agents.assistant import Assistant
from app.core.agents.assistant_guideline import GuidelineAssistant
from .definitions import (
    llm_cfg,
    MEDICAL_SYSTEM_MESSAGE,
    RAG_SYSTEM_MESSAGE,
    MEDICAL_FUNCTIONS
)


class AgentFactory:
    """
    统一的机器人实例工厂类，支持 key-value 形式的访问
    使用单例模式确保工厂实例唯一性
    """

    _instance: Optional['AgentFactory'] = None
    _agents: Dict[str, Union[ReActChat, Assistant,GuidelineAssistant]]

    def __new__(cls) -> 'AgentFactory':
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
        return cls._instance

    def __init__(self):
        """初始化工厂，注册所有机器人实例"""
        if not hasattr(self, '_initialized'):
            self._register_agents()
            self._initialized = True

    def _create_react_bot(self) -> ReActChat:
        """创建公积金助手实例"""
        return ReActChat(
            llm=llm_cfg,
            system_message=MEDICAL_SYSTEM_MESSAGE,
            function_list=MEDICAL_FUNCTIONS
        )

    def _create_rag_bot(self) -> Assistant:
        """创建基础助手实例"""
        return Assistant(llm=llm_cfg)
    
    def _create_guideline_rag_bot(self) -> GuidelineAssistant:
        """带有行动指南的Agent"""
        return GuidelineAssistant(llm=llm_cfg)
    

    def _create_realtime_bot(self) -> ReActChat:
        """创建公积金助手实例"""
        return ReActChat(
            llm=llm_cfg,
            system_message=MEDICAL_SYSTEM_MESSAGE,
            function_list=MEDICAL_FUNCTIONS
        )



    def _register_agents(self):
        """注册所有可用的机器人实例"""
        # 创建机器人实例
        react_bot_instance = self._create_react_bot()
        rag_bot_instance = self._create_rag_bot()
        guideline_bot_instance = self._create_guideline_rag_bot()

        self._agents = {
            # 原始键名
            'react_bot': react_bot_instance,
            'rag_bot': rag_bot_instance,
            'guideline_bot': guideline_bot_instance,
        }

    def get_agent(self, agent_key: str) -> Union[ReActChat, Assistant, GuidelineAssistant]:
        """
        根据键名获取对应的机器人实例

        Args:
            agent_key: 机器人键名

        Returns:
            对应的机器人实例

        Raises:
            KeyError: 当键名不存在时
        """
        if agent_key not in self._agents:
            available_agents = list(self._agents.keys())
            raise KeyError(f"机器人 '{agent_key}' 不存在。可用的机器人: {available_agents}")

        return self._agents[agent_key]

    def get_agent_safe(self, agent_key: str, default_agent: str = 'bot') -> Union[ReActChat, Assistant,GuidelineAssistant]:
        """
        安全获取机器人实例，如果键名不存在则返回默认机器人

        Args:
            agent_key: 目标机器人键名
            default_agent: 默认机器人键名，默认为 'bot'

        Returns:
            对应的机器人实例或默认机器人实例
        """
        try:
            return self.get_agent(agent_key)
        except KeyError:
            return self.get_agent(default_agent)

    def list_agents(self) -> list[str]:
        """
        获取所有可用的机器人键名列表

        Returns:
            机器人键名列表
        """
        return list(self._agents.keys())

    def get_agent_info(self, agent_key: str) -> Dict[str, str]:
        """
        获取指定机器人的详细信息

        Args:
            agent_key: 机器人键名

        Returns:
            包含机器人信息的字典
        """
        agent = self.get_agent(agent_key)
        agent_class = agent.__class__.__name__

        # 根据不同的 agent 类型返回不同的描述
        descriptions = {
            'ReActChat': '公积金政务服务助手 - 支持 ReAct 思维链和工具调用',
            'Assistant': '通用对话助手 - 基础问答功能',
            'QwenRagAssistant': 'RAG 增强助手 - 支持知识库检索增强'
        }

        return {
            'key': agent_key,
            'class': agent_class,
            'description': descriptions.get(agent_class, '未知类型的助手'),
            'type': agent_class
        }

    def __getitem__(self, key: str) -> Union[ReActChat, Assistant, GuidelineAssistant]:
        """支持字典式访问 agent_factory['bot']"""
        return self.get_agent(key)

    def __contains__(self, key: str) -> bool:
        """支持 'bot' in agent_factory 语法"""
        return key in self._agents

    def __repr__(self) -> str:
        """返回工厂的字符串表示"""
        return f"AgentFactory(agents={len(self._agents)}, keys={list(self._agents.keys())})"


# 创建全局工厂实例（单例）
agent_factory = AgentFactory()