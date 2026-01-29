from app.model.message import Message,MessageRead
from app.model.chat import Chat, ChatStatusEnum
from app.model.message_context import ChatContext, ContextType,ChatContextRead
from app.config.database import get_db, SessionLocal
from typing import List, Optional
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from qwen_agent.llm.schema import Message as QwenMessage
import json
import logging

import time
import random
import string

# ... (Previous imports are kept as they are needed for the full context if this file was standalone, 
# but specifically for assistant.py, we need the imports below)
import copy
import json
import time
import uuid
from typing import Dict, Iterator, List, Literal, Optional, Union

from qwen_agent.agents.fncall_agent import FnCallAgent
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import CONTENT, ROLE, SYSTEM, USER, ContentItem, Message  # DEFAULT_SYSTEM_MESSAGE
from qwen_agent.log import logger
from qwen_agent.tools import BaseTool
from app.core.tools.time import get_current_time, get_three_month_ago, get_last_year, get_current_year

from app.core.rag.knowledge_search import (
    KnowledgeSearchService,
    format_knowledge_to_source_and_content
)

from app.core.text_formatter import format_text_for_markdown
import re

# 优化后的系统提示词：增加了思维链引导和更严格的逻辑约束
DEFAULT_SYSTEM_MESSAGE='''你是厦门市公积金政务服务助手小金灵。在回答用户问题之前，请严格遵循以下思考和回答流程：

## 💡 思考与决策流程 (Thought Process)
1.  **意图识别**：首先明确用户是想办理业务（提取、贷款）、查询信息（额度、进度）还是咨询政策条件。
2.  **条件匹配**：检查用户是否提供了关键条件（户籍地、购房地、参保状态、时间节点）。
    - 若条件缺失且影响判断（如“离职提取”未说明户籍），必须优先礼貌追问。
3.  **知识验证**：在下文提供的【知识库】中寻找证据。
    - **严格匹配**：禁止仅凭关键词匹配，必须确认政策适用的前提条件（如时间范围、适用人群）与用户情况一致。
    - **冲突解决**：若多条知识存在冲突，优先采信【行动指南】或发布时间较新的政策。
4.  **答案构建**：
    - 直接回答核心结论（能/不能/需要xx材料）。
    - 分点陈述细节，确保逻辑清晰。
    - 附上来源引用。

## 核心规则
1.  **精准识别用户核心诉求**
    聚焦用户问题指向的公积金业务类型。特别注意区分：
    - 关键识别：
        - 用户提问“在X地购房，如何提取公积金？” -> **理解为提取厦门公积金用于X地购房**。
        - 用户提问“提取X地公积金” -> **理解为提取异地公积金**（通常需引导至当地中心）。
2.  **严格区分政策适用范围**
    明确区分：本市/省内/省外、本地户籍/外地户籍、单位职工/灵活就业。
    - 例：代际互助业务仅限 2025.2.1-2025.12.31 期间。
3.  **主动排除干扰项**
    排除医保、社保、税务等非公积金内容，即使检索到了相关片段。
4.  **常识性与无内容处理**
    - 常识性问题（如“装修”、“买车位”）直接回答“不能”并简述原因。
    - 无法确定或无相关政策：直接回复“当前未检索到直接相关的政策条文，请咨询0592-12345-1-0公积金专席。”

## 知识库内容回答原则
1.  **先结论后细节**：先回答“能”或“不能”，再展开。
2.  **来源核验**：严禁编造知识库中不存在的信息。
3.  **多问题分点**：用户涉及多个问题时，分点作答。
4.  **保留官方链接**：回答中保留官网链接。

## 关键业务政策速查（高频易错点）
- **离职/失业提取**：
    - **厦门户籍**：**不能**办理离职/失业提取（必须退休或满足其他条件）。
    - **外地户籍**：需账户封存满6个月，且未在异地继续缴存。
- **购房提取**：
    - **冲抵本金**：**仅限厦门本市**房产。
    - **异地购房**：**不能冲抵本金**，仅能“按年提取报销贷款本息”。
    - **提取条件**：异地购房需满足“户籍地”或“工作地”在购房地。
- **租房提取**：
    - 线上无法查询终止时间。
    - 租房提取与购房/还贷业务可能互斥，需提示用户。
- **代际互助**：
    - 仅限父母与子女之间，不包括兄弟姐妹或祖孙。
- **办理渠道**：
    - 线下提取业务通常去**贷款银行网点**（岛内/岛外区分），而非缴存银行。

## 引用标注规则
1.  引用格式：[来源:[文档ID](文档ID)]。
2.  仅引用真正支持你回答的文档，不要凑数。

## 禁止回答规则
1.  非公积金相关话题（政治、娱乐等）不予回答。
2.  明确咨询“如何提取异地公积金”的，引导咨询当地。
'''

KNOWLEDGE_TEMPLATE = """# 知识库
{knowledge}"""

KNOWLEDGEGRAPG_TEMPLATE = '''# 知识图谱 (关联关系参考)
{knowledgegraph}
'''

KNOWLEDGE_SNIPPET = """## 来自 {source} 的内容：

{content}
"""

BASE_INFO_TEMPLATE = """ # 基础上下文信息

## 时间参照
当前系统时间: {current_time}
至今三个月前：{three_month}
去年: {last_year}
今年: {current_year}
"""

DATA_INFO_TEMPLATE= """ # 表格数据详情
- **使用说明**：以下数据来自政策表格，请结合上下文作答。
{data}
"""


class Assistant(FnCallAgent):
    """This is a widely applicable agent integrated with RAG capabilities and function call ability."""

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None,
                 rag_cfg: Optional[Dict] = None):
        
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message=system_message,
                         name=name,
                         description=description,
                         files=files,
                         rag_cfg=rag_cfg)
        self.full_text = ""
        self.current_knowledge = ""
        self.supp_text = ""
        self.knowledge_data = {}
        self.sources = []


    def _run(self,
             messages: List[Message],
             lang: Literal['en', 'zh'] = 'zh',
             knowledge: str = '',
             **kwargs) -> Iterator[List[Message]]:
        """Q&A with RAG and tool use abilities.

        Args:
            knowledge: If an external knowledge string is provided,
              it will be used directly without retrieving information from files in messages.

        """

        new_messages = self._prepend_knowledge_prompt(messages=messages, lang=lang, knowledge=knowledge, **kwargs)
        return super()._run(messages=new_messages, lang=lang, **kwargs)

    def _prepend_knowledge_prompt(self,
                                  messages: List[Message],
                                  knowledge: str = '',
                                  **kwargs) -> List[Message]:
        messages = copy.deepcopy(messages)
        response_keywords = []
        query = None

        if not knowledge:
            query = KnowledgeSearchService.extract_query_from_messages(messages)

        # 知识库检索
        knowledge_graph_prompt=""
        excel_data_prompt = ""
        if not knowledge and query:
            # 使用统一的知识检索服务
            # [修改点 1 & 2] 增加 doc_top_n 数量，启用知识图谱搜索
            knowledge_data, graph_data, excel_data = KnowledgeSearchService.search_and_integrate_knowledge(
                query=query,
                doc_top_n=10,        # 增加召回数量，原为 5
                graph_top_n=3,
                enable_graph_search=True # 启用图谱搜索，增强复杂问题推理
            )

            if knowledge_data:
                knowledge = KnowledgeSearchService.format_knowledge_for_prompt(knowledge_data)

                self.knowledge_data = knowledge_data

            if graph_data:
                knowledge_graph_prompt = KNOWLEDGEGRAPG_TEMPLATE.format(knowledgegraph=graph_data)
            
            if excel_data:
                excel_data_prompt = DATA_INFO_TEMPLATE.format(data=excel_data)
                
        if knowledge:
            knowledge_prompt = format_knowledge_to_source_and_content(knowledge)
        else:
            knowledge_prompt = []

        
        
        snippets = []
        references = {}
        for k in knowledge_prompt:
            snippets.append(KNOWLEDGE_SNIPPET.format(source=k['source'], content=k['content']))
            references[k['source']] = k['content']
        knowledge_prompt = ''
        if snippets:
            knowledge_prompt = KNOWLEDGE_TEMPLATE.format(knowledge='\n\n'.join(snippets))

        #logger.info(f"材料中出现关键信息: {keyword_prompt}")


        base_info_prompt = BASE_INFO_TEMPLATE.format(
            current_time=get_current_time(),
            three_month=get_three_month_ago(),
            last_year=get_last_year(),
            current_year=get_current_year()
        )


        if knowledge_prompt:
            if messages and messages[0][ROLE] == SYSTEM:
                if isinstance(messages[0][CONTENT], str):
                    messages[0][CONTENT] += '\n\n' + knowledge_prompt + '\n\n'
                else:
                    assert isinstance(messages[0][CONTENT], list)
                    messages[0][CONTENT] += [ContentItem(text='\n\n' + knowledge_prompt + '\n\n' )]
            else:
                # 重新组合 System Prompt，确保逻辑连贯
                full_system_content = (
                    f"{DEFAULT_SYSTEM_MESSAGE}\n\n"
                    f"{base_info_prompt}\n\n"  # 基础信息前置，建立时间上下文
                    f"{knowledge_prompt}\n\n"
                    f"{knowledge_graph_prompt}\n\n"
                    f"{excel_data_prompt}"
                )
                messages = [Message(role=SYSTEM, content=full_system_content), messages[-1]]
        self.source = references

        #logger.info(f'最后提示词:{messages[0][CONTENT]}')
        return messages
    



        
    
    def _run_openai_format(
        self,
        messages: List[Message],
        lang: Literal['en', 'zh'] = 'zh',
        knowledge: str = '',
        **kwargs
    ) -> Iterator[str]:
        """Q&A with RAG and tool use abilities in OpenAI format.

        Args:
            knowledge: If an external knowledge string is provided,
              it will be used directly without retrieving information from files in messages.

        """
        # 使用与 _run 相同的逻辑
        new_messages = self._prepend_knowledge_prompt(messages=messages, lang=lang, knowledge=knowledge, **kwargs)
        #logger.info(f'new_messages:{new_messages}')

        chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())
        model = "xmtelecom"
        # 发送obs帧 - 检查是否有实质性的知识库内容
        # no_response = True #上线前改True
        if bool(self.source):
            #no_response = False 
            obs_chunk  = {
                    "id": chunk_id,
                    "object": "chat.completion.observation",
                    "created": created,
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": json.dumps(self.source,ensure_ascii=False)},
                        "finish_reason": None
                    }]
                }
            yield f"data: {json.dumps(obs_chunk, ensure_ascii=False)}\n\n"
        else:
            logger.info('Skipping obs chunk due to insufficient content')

        

        # 调用父类的 _run 方法，但转换输出格式为 OpenAI 流式格式
        chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
        model = "xmtelecom"

        # 发送开始帧
        start_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(start_chunk, ensure_ascii=False)}\n\n"




        # 主要回答生成
        try:
            # 生成主要回答，不传递prev_full_text避免重复
            yield from self.call_llm_with_messages(chunk_id=chunk_id,
                                                   model=model,
                                                   messages=new_messages,
                                                   lang='zh')

        except Exception as e:
            logger.error(f"Error in main response generation: {e}")
            # 发送错误消息给用户
            error_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": "\n抱歉，生成回答时遇到问题，请稍后重试。"},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        

        # 发送结束帧
        final_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        #yield "data: [DONE]\n\n"


    def call_llm_with_messages(self, chunk_id, model, messages: List[Message], lang, **kwargs):
        """
        调用LLM生成流式响应

        Args:
            prev_full_text: 之前的文本内容（避免重复输出时使用）
            is_supplement: 是否为补充说明
        """
        for message_batch in super()._run(messages=messages, lang=lang, **kwargs):
            if message_batch and message_batch[-1]:
                content = message_batch[-1].get(CONTENT, '')
                if content:
                    if isinstance(content, str):
                        text_content = content
                    else:
                        # 处理 ContentItem 列表
                        text_content = ""
                        for item in content if isinstance(content, list) else []:
                            if hasattr(item, 'text'):
                                text_content += item.text

                    
                    self.full_text = text_content
                    self.sources = self._extract_content_ref(text_content)
                    delta = {"content": text_content}
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": delta,
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        # 带索引：
        
        if self.sources:
            references = [k['reference'] for k in self.knowledge_data if k['url'] in self.sources and k['reference'] is not None]
            reference = []
            for k in references:
                item = k.split('\n')
                for i in item:
                    if i not in reference:
                        reference.append(i)
            self.supp_text = "\n\n".join(reference)
            if len(reference):
                delta = {"content": f'{self.full_text}\n\n**参考出处**\n\n{self.supp_text}'}
            else:
                delta = {"content": f'{self.full_text}\n\n'}
            #delta = { "content": f'{self.full_text}',"source": reference}
            
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": delta,
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    def _extract_content_ref(self, full_text: str) -> List[str]:
        """正则表达式提取所有的字符串
            例如 [来源: [3](3)] 你应该得到 [3]

            [来源: [2](2), [7](7),[34](34),[46](46),[graph_chunk](graph_chunk), +more)]。
            得到 [2,7,34,46,graph_chunk]

            [来源: [doc_12579] 得到 doc_12579
        """
        import re

        result = []
        seen = set()

        # 模式1: 匹配 [来源: [内容](链接)] 格式
        pattern1 = r'\[来源:\s*\[([^\]]+)\]\([^)]+\)\]'
        matches1 = re.findall(pattern1, full_text)

        # 模式2:
        pattern2 = r'(?:doc_\d{5}|\d{5})'
        matches2 = re.findall(pattern2, full_text)

        # 合并所有匹配结果
        all_matches = matches1 + matches2

        # 去重并保持顺序
        for match in all_matches:
            if match not in seen:
                seen.add(match)
                result.append(match)

        return result