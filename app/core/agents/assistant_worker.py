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
#
# Original Source: Based on qwen-agent framework

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

from app.core.rag.knowledge_search import (
    KnowledgeSearchService,
    format_knowledge_to_source_and_content
)
from app.core.rule.intent import IntentClassifier
from app.core.agents.prompts import get_prompt_by_question

#若缺少关键信息（如参保月份、原参保地、是否连续参保），请主动、礼貌地追问。

DEFAULT_SYSTEM_MESSAGE='''你是厦门市医保政务服务助手小E。你必须严格遵守以下规则：

**核心原则：**
如果您不知道答案，或者提供的报告不包含足够的信息来提供答案，请直接说不知道。不要编造任何东西。
最终回答应从报告中删除所有不相关的信息，并将清理后的信息合并为一个全面的答案，该答案提供适合回答长度和格式的所有关键点和含义的解释。
回答应保留 "应", "可能" 或 "将" 等情态动词的原始含义和用法。
回答还应保留分析师报告中包含的所有数据引用，但不要提及分析过程中多个分析师的角色。
**不要在单个引用中列出超过 5 个记录 ID**。相反，列出前 5 个最相关的记录 ID，并添加 "+more" 以表明还有更多。

例如: 
"X 是 Y 公司的所有者，受到多项不法行为指控 [来源: [2](2), [7](7),[34](34),[46](46),[64](64), +more)]。
他还是 X 公司的首席执行官 [来源: [3](3)"
其中 1, 2, 3, 7, 34, 46 和 64 代表相关数据记录的 source 。
不要包含未提供支持证据的信息。

**禁止**
医保无关话题禁止回答
政治话题禁止回答

'''

KNOWLEDGE_TEMPLATE = """# 知识库
{knowledge}"""

KNOWLEDGE_KEY_WORDS = """# 关键信息(非常重要，回复里要注明)
{keywords}
"""

KNOWLEDGE_SNIPPET = """## 来自 {source} 的内容：

```
{content}
```"""







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
        self.classifier = IntentClassifier()


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
        if not knowledge and query:
            # 使用统一的知识检索服务
            knowledge_data, response_keywords = KnowledgeSearchService.search_and_integrate_knowledge(
                query=query,
                doc_top_n=5,
                graph_top_n=3,
                enable_graph_search=True
            )

            if knowledge_data:
                knowledge = KnowledgeSearchService.format_knowledge_for_prompt(knowledge_data)
                
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

        # 使用意图分类器生成提示词
        intent_prompt = ""
        if query:
            try:
                intent_prompt = get_prompt_by_question(query, self.classifier)
                logger.info(f"意图识别提示词: {intent_prompt}")  # 记录前100个字符
            except Exception as e:
                logger.error(f"意图分类失败: {e}")
                intent_prompt = ""

        # 如果有意图提示词，优先使用意图提示词；否则使用关键词提示词
        if intent_prompt:
            keyword_prompt = intent_prompt
            
        else:
            keyword_prompt = KNOWLEDGE_KEY_WORDS.format(keywords=",".join(set(response_keywords)))
        #logger.info(f"材料中出现关键信息: {keyword_prompt}")

        if knowledge_prompt:
            if messages and messages[0][ROLE] == SYSTEM:
                if isinstance(messages[0][CONTENT], str):
                    messages[0][CONTENT] += '\n\n' + knowledge_prompt + '\n\n' + keyword_prompt
                else:
                    assert isinstance(messages[0][CONTENT], list)
                    messages[0][CONTENT] += [ContentItem(text='\n\n' + knowledge_prompt + '\n\n' + keyword_prompt)]
            else:
                messages = [Message(role=SYSTEM, content=f"{DEFAULT_SYSTEM_MESSAGE}\n\n{knowledge_prompt}\n\n{keyword_prompt}"),
                            messages[-1]]
        self.source = references

        logger.info(f'最后提示词:{messages[0][CONTENT]}')
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

                    delta = {"content": text_content}
                    self.full_text = text_content

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


    def call_llm_with_messages_supp(self, chunk_id, model, messages: List[Message], lang, prev_context, **kwargs):
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
                                
                    delta = {"content": f"{prev_context} \n\n {text_content}"}
                    self.full_text = f"{prev_context} \n\n {text_content}"

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
