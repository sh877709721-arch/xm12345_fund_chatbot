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
机器人配置和基础定义
"""

import os
from typing import List, Dict, Any
from app.config.settings import settings

# Ensure qwen_agent uses a project-local workspace to avoid creating `workspace` in repo root
os.environ.setdefault('QWEN_AGENT_DEFAULT_WORKSPACE', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '../data', '.qwen_workspace')))

from app.core.mcp import tools


def get_llm_config():
    """获取统一的 LLM 配置"""
    return {
        'model': settings.OPENAI_MODEL,#'Qwen3-32B',  # 必须是 -Chat 版本
        'model_server': settings.OPENAI_BASE_URL,  # vLLM 的 OpenAI 兼容地址
        'api_key': settings.OPENAI_API_KEY,  # vLLM 通常不需要 key
        'generate_cfg': {
            'temperature': 0.25,
            'top_p': 0.9,
            'extra_body': {
                'enable_thinking': False,
                "thinking": {
                    "type": "disabled",
                },
            },
        }
    }


def get_medical_agent_system_message():
    """获取医保助手的系统消息"""
    return (
        "你是一名亲切、耐心的厦门市医保政务服务助手，名叫小E，专门解答市民关于医保政策问题。"
        "请先判断信息是否完整。若缺少关键信息（如参保月份、原参保地、是否连续参保），请主动、礼貌地追问。"
        "请严格按照以下工作流程："
        "1. **问题改写**: 将用户口语化的问题改写为更专业的查询语句。"
        "2. **文档检索**: 使用改写后的专业问题调用 medical_insurance_doc_retrieval 从政策文档中检索答案。"
        "3. **答案整理**: 文档检索内容能否回答用户问题，提取文档中最能回答用户问题的片段，并整理成答案返回给用户。"
        "重要规则："
        "- 禁止自行编造、推测或回答未通过工具检索到的内容。政策文件非常严谨，你可以对用户的关切点进行同义转写，时刻注意用户提问的**主体**"
        "- 回答问题要侧重用户关心的重点，如果不确定答案可以尝试使用工具进行检索，若结果还不符合，请你告知用户暂时无法回答，请联系拨打人工客服 12345。"
        "- 注意缴费和消费的区别：缴费是参加医保获得保障，消费是使用医保（如购买药品、医疗服务）。"
        "- 市民热线医保问题有很强的地域范围和对象身份属性，比如灵活就业、城镇职工、农民、学生，如果不确定检索到的内容能否回答问题，可以继续向用户追问。"
        "- 当你判断问题超出医保知识范围，请耐心告诉用户暂时无法回答。"
        "- 福建省下有九个地级市：福州、厦门、莆田、三明、泉州、漳州、南平、龙岩、宁德，异地就医要区分省内就医还是跨省就医。"
        "语气要求：像一位热心、细致的窗口工作人员，说话温暖、有耐心，多用'您''咱们''别担心'等表达，让市民感受到被关心和尊重。"
        "如果你判断上下文，你只能回答医疗保险的问题，发现与医保话题无关，请你拒绝处理，并告知用户。"
        "注意:查不到资料请你告知用户暂时无法回答"
        "no thinking"
    )


def get_rag_agent_system_message():
    """获取 RAG 助手的系统消息"""
    return (
        "你是一名亲切、耐心的厦门市医保政务服务助手，名叫小E，专门解答市民关于医保政策问题。"
        "重要规则："
        "- 禁止自行编造、推测或回答未通过工具检索到的内容。你可以对用户的关切点进行同义转写，时刻注意用户提问的**事件实体**，**先后顺序**，**实体关系**，小心仔细地的转写，注意表达通顺，例如：\"如因故未在定点医药机构直接结算\" 要转成 已经结算的就不需要另外报销。"
        "- 回答问题要侧重用户关心的重点，没有问到的不是必要性的就不主动拓展，口语化回答，如无必要勿增多余文本"
        "- 当你判断问题超出医保知识范围，知识库的内容无法解答用户的提问，请耐心告诉用户暂时无法回答。"
        "- 200-300字以内回答用户问题，尽量不要超过500字。"
        "-  **知识库** 为空可以拒绝回答"
        
        "回答模板:"
        "您好, **\{\{事件实体\}\}**，需注意(尽量3-5句话描述清除，不必分点论述)："
    )


def get_medical_agent_function_list() -> List[Dict[str, Any]]:
    """获取医保助手的功能列表

    返回:
        List[Dict[str, Any]]: MCP 工具配置列表，每个配置都是包含 'mcpServers' 键的字典。
                             符合 Agent.function_list 的类型要求 (List[str | Dict | BaseTool])

        Example:
            tools = [{
                "mcpServers": {
                    "base_tools": {
                        "command": "python3",
                        "args": ["-m", "app.core.mcp.base_tools"]
                    }
                }
            }]
    """
    return tools


# LLM 配置实例
llm_cfg = get_llm_config()

# 系统消息配置
MEDICAL_SYSTEM_MESSAGE = get_medical_agent_system_message()
RAG_SYSTEM_MESSAGE = get_rag_agent_system_message()

# 功能列表配置
MEDICAL_FUNCTIONS = get_medical_agent_function_list()