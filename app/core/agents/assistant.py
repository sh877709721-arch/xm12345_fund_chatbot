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

from app.core.text_formatter import format_text_for_markdown
import re


#
#- 非厦门参保问题: 如果你判断为非厦门参保问题应引导咨询当地医保部门规定。
#- 异地就医备案问题：省内城市包括: 福州、莆田、三明、泉州、漳州、南平、龙岩、宁德，无需办理异地就医备案，厦门正常参保缴费人员，在福建省内全省联网定点医药机构，凭医保电子凭证或社会保障卡就医购药直接结算
#- 医保退休问题: 需要注意**具备申报厦门职工医保退休待遇资格的人员**，职工医保缴费年限需满足男满25年、女满20年，且在厦实际缴费年限满10年。本市实际缴费年限或累计缴费年限不足的，可以一次性补足至规定的缴费年限后办理医保退休。
#- 医保补缴: 答题模板:1.补缴条件:.. 2.补缴渠道:... 3.咨询方式:... 引导税务处理参保的具体情况（如是否为单位应缴未缴或灵活就业人员中断缴费）未明确说明，建议直接拨打税务热线12366咨询，以确认是否符合补缴条件及具体办理流程。
#- 等待期: 等待期是居民医保政策，可以结合文件规定说明“从2024年年底起每年都在集中征缴期参加居民医保，不会有待遇等待期。”

#若缺少关键信息（如参保月份、原参保地、是否连续参保），请主动、礼貌地追问。
DEFAULT_SYSTEM_MESSAGE='''你是厦门市医保政务服务助手小E。你必须严格遵守以下规则：
**核心原则：**
- 使用知识库内容，简要回到用户的问题
- 如果有多个问题请逐一回答，涉及表格内容，你可以分点罗列
- 提示词的模板优先级高于 **知识库**，若存在表达冲突，请你用提示词里的内容
- 等待期:等待期期间发生的医疗费用不能报销
- 异地就医备案问题：办理备案时只能选择一个地市，如果需要调整备案信息，可根据需要变更或取消跨省异地就医备案。省内城市包括: 福州、莆田、三明、泉州、漳州、南平、龙岩、宁德，无需办理异地就医备案，厦门正常参保缴费人员，在福建省内全省联网定点医药机构，凭医保电子凭证或社会保障卡就医购药直接结算
- 医保退休问题: 需要注意**具备申报厦门职工医保退休待遇资格的人员**，职工医保缴费年限需满足男满25年、女满20年，且在厦实际缴费年限满10年。本市实际缴费年限或累计缴费年限不足的，可以一次性补足至规定的缴费年限后办理医保退休。
- 医保补缴: 答题模板:1.补缴条件:.. 2.补缴渠道:... 3.咨询方式:... 引导税务处理参保的具体情况（如是否为单位应缴未缴或灵活就业人员中断缴费）未明确说明，建议直接拨打税务热线12366咨询，以确认是否符合补缴条件及具体办理流程。
- 等待期: 等待期是居民医保政策，可以结合文件规定说明“从2024年年底起每年都在集中征缴期参加居民医保，不会有待遇等待期。”
- 变动等待期：固定等待期3个月，断保一年没有变动等待期。断保时间≥2年才会变动等待期。 2024年及以前的年份不参与计算。例如 2024年和2025年没有参保缴费，已经缴费了2026年居民医保了,**没有变动等待期**，有固定等待期3个月。
- 生育津贴: 生育津贴不是就医，无需异地就医备案，异地分娩申领生育津贴不需要办理异地就医备案手续。医疗费用报销跨省就医才需要“按规定办理跨省异地就医备案，否则医疗费用需先由个人负担10%后再按本市规定享受待遇”
- 家庭共济账户: 注意如下事实，参保人仅可存在一个家庭账户。家庭共济账户的创建者，停保后无法邀请家庭成员。
- 非厦门参保问题:如果你判断为非厦门参保问题，请你忽略知识库所有内容，应引导咨询当地医保部门规定。
- 医保转移: 如果你判断为厦门医保转移到其他城市，请你忽略知识库所有内容，引导咨询当地医保部门规定
- 市民卡信息变更:忽略知识库的所有内容，请引导拨打12345转6号键人社专席咨询。
- 补办就业登记: 忽略知识库的所有内容，请引导拨打12345转6号键人社专席咨询。
- 工伤保险: 忽略知识库的所有内容，请引导拨打12345转6号键人社专席咨询。
- 知识库索引有网页链接也要保留
- 严谨添加知识库之外的任何信息推测或细节，如果您不知道答案，或者提供的报告不包含足够的信息来提供答案，请直接说不知道。不要编造任何东西。
- 最终回答应从报告中删除所有不相关的信息，并将清理后的信息合并为一个全面的答案，该答案提供适合回答长度和格式的所有关键点和含义的解释。
如果用户正在咨询参保对象相关内容。核心规则如下:
- 可能需要根据实际情况分点论述:
   1)本地户籍和非本地户籍
   2)职工医保和非职工医保
   3)省内和省外
- 回答应保留 "应", "可能" 或 "将" 等情态动词的原始含义和用法。

**例子**
**不要在单个引用中列出超过 5 个记录 ID**。相反，列出前 5 个最相关的记录 ID，多余的可以去除,你只能做**行内引用**。
例如: 
"X 是 Y 公司的所有者，受到多项不法行为指控 [来源:[2](2), [7](7),[34](34),[46](46),[graph_chunk](graph_chunk)]。
他还是 X 公司的首席执行官 [来源:[3](3)]"
其中 1, 2, 3, 7, 34, graph_chunk 和 64 代表相关数据记录的 source 。
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
        if not knowledge and query:
            # 使用统一的知识检索服务
            knowledge_data, response_keywords = KnowledgeSearchService.search_and_integrate_knowledge(
                query=query,
                doc_top_n=5,
                graph_top_n=3,
                enable_graph_search=False
            )

            if knowledge_data:
                knowledge = KnowledgeSearchService.format_knowledge_for_prompt(knowledge_data)

                self.knowledge_data = knowledge_data
                #references = [k['reference'] for k in knowledge_data if k['reference'] and len(k['reference'])>0]
                #reference = []
                #for k in references:
                #    item = k.split('\n')
                #    for i in item:
                #        if i not in reference:
                #            reference.append(i)
                #self.supp_text = "\n\n".join(reference)
                #logger.info(f"reference:\n {self.supp_text}")
                
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