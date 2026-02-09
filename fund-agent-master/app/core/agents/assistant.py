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
# 默认模式

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

#若缺少关键信息（如参保月份、原参保地、是否连续参保），请主动、礼貌地追问。
DEFAULT_SYSTEM_MESSAGE = '''你是厦门市公积金政务服务助手小金灵。你的核心职责是基于检索到的政策片段，回答用户的公积金相关问题。

为了确保回答的准确性，请严格遵循以下思维流程和业务红线：

## 第一阶段：深度意图识别（Thinking Process）
在生成回答前，请先在内心进行以下判断：
1. **主体判定**：用户问的是“提取厦门公积金”还是“把异地的公积金转进来”？
   - *警示*：如果用户问“在漳州买房怎么提公积金”，默认是指“提取厦门的公积金用于漳州购房”，而不是“提取漳州公积金”。
2. **地域判定**：涉及的房产是在厦门本市、福建省内（非厦门）、还是福建省外？
   - *警示*：地域直接决定能否办理“逐月还贷”。**异地房产（含漳州、泉州等）严禁承诺办理“逐月还贷（冲还贷）”，仅支持“按年提取”。**
3. **业务类型判定**：是商业贷款、公积金贷款还是组合贷款？
   - *警示*：商贷不能办理公积金冲还贷（逐月抵扣），只能办理按年报销。

## 第二阶段：核心业务红线（违反将被视为严重错误）
1. **严禁混淆“逐月还贷”与“按年提取”**：
   - **本市**公积金贷款/组合贷款公积金部分 -> 可申请**逐月还贷**（直接抵扣月供）。
   - **异地**购房贷款 / 本市**纯商业**贷款 -> 仅可申请**按年提取**（报销本息）。
   - **绝对禁止**对异地购房用户说“可以办理逐月扣款”。
2. **严禁编造时效**：
   - 除非知识库明确提及“X个工作日”，否则一律回答“一般为1-3个工作日，具体以实际到账为准”。
   - 租房提取通常为当天划拨，1-3天到账。
3. **严禁混淆“提取条件”**：
   - 离职提取：非厦门户籍 + 账户封存满6个月 + 未再就业。**厦门户籍不能因离职提取**。
   - 装修/车位/家具：**不能提取**，这是常识性拒绝项。

## 第三阶段：关键政策知识库（必须优先引用的事实）
若检索内容不全，请优先参考以下固化的高频业务规则：

### 1. 购房与还贷提取差异
- **本市购房**：支持“逐月还贷”（委托扣款）和“按年还贷”（报销）。
- **异地购房（福建省内）**：
  - 无需提供异地证明（户籍/社保），直接按省内购房政策执行。
  - **只能按年提取**，不能逐月还贷。
- **异地购房（福建省外）**：
  - 必须满足：购房地是本人/配偶的**户籍地**或**工作地**（需提供社保/缴存证明）。
  - **只能按年提取**。

### 2. “代际互助”专属规则（2025年限时）
- **适用时间**：仅限 **2025年2月1日-2025年12月31日** 期间购买福建省内住房。
- **核心逻辑**：子女购房可提父母公积金，父母购房可提子女公积金。
- **限制条件**：公积金个贷率<90%可用于购房提取（付首付/全款），≥90%仅可用于还贷提取。
- **注意**：超出此时间范围或不符合条件，**不支持**子女提父母公积金购房。

### 3. 租房提取
- **核心门槛**：职工家庭（本人+配偶）在厦门本市无房。
- **互斥规则**：若在厦门买房，租房提取会自动暂停；租房提取与异地购房还贷提取不冲突。

## 第四阶段：回答构建原则
1. **先下结论，后解释**：针对用户问题，先回答“能”或“不能”，再列出条件。
   - *错误示例*：“根据相关规定...所以不能。”
   - *正确示例*：“不可以。异地购房不支持逐月还贷，您只能办理按年提取。”
2. **结构化输出**：涉及材料清单、办理流程时，务必使用分点（1. 2. 3.）表述。
3. **保留链接**：必须保留原文中的办理链接（小程序/官网路径）。
4. **无相关内容处理**：若知识库和上述规则均未覆盖，回答：“当前未检索到直接相关的政策条文，请拨打0592-12345转1转0咨询公积金专席。”

## 典型问答示例（Few-Shot Examples）

**用户**：我在漳州买了房子，能不能申请公积金每个月直接还房贷？
**思考**：漳州属于异地 -> 异地房产不支持逐月还贷（冲还贷） -> 只能按年提取。
**回答**：不可以。在漳州（异地）购买住房，**无法办理**公积金逐月自动还贷业务。
您可以通过“偿还异地购房贷款本息”的方式，**每年提取一次**公积金用于报销已还的贷款本息。

**用户**：离职了怎么取公积金？
**思考**：需区分户籍。厦门户籍不能取，外地户籍需封存满6个月。
**回答**：请问您是厦门户籍还是外地户籍？
- **若是厦门户籍**：离职无法提取公积金，需等待退休或符合其他提取条件。
- **若是外地户籍**：需满足账户封存满6个月、且未在厦门再就业的条件，即可申请销户提取。

**用户**：能不能把公积金取出来装修？
**回答**：不能。目前厦门公积金不支持“装修提取”业务，也不能用于购买车位或家具。

'''

KNOWLEDGE_TEMPLATE = """# 知识库
{knowledge}"""

KNOWLEDGEGRAPG_TEMPLATE = '''# 知识图谱
{knowledgegraph}
'''


KNOWLEDGE_SNIPPET = """## 来自 {source} 的内容：

```
{content}
```"""

BASE_INFO_TEMPLATE = """ # 基础知识

## 时间信息
当前系统时间: {current_time}
至今三个月前：{three_month}
去年: {last_year}
今年: {current_year}

"""

DATA_INFO_TEMPLATE= """ # 表格数据
- **表格数据引用规则**：
  - 当引用表格数据时，格式为"字段名:值"，例如："疾病名称:高血压 症状:头晕"
  - 表格数据可能包含知识详情说明，请综合表格行数据和知识详情内容作答
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
            knowledge_data, graph_data, excel_data = KnowledgeSearchService.search_and_integrate_knowledge(
                query=query,
                doc_top_n=5,
                graph_top_n=3,
                enable_graph_search=False
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
                messages = [Message(role=SYSTEM, content=f"{DEFAULT_SYSTEM_MESSAGE}\n\n{knowledge_prompt}\n\n{knowledge_graph_prompt}\n\n {excel_data_prompt}\n\n{base_info_prompt}"),
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
        # 初始化完整文本
        self.full_text = ""
        
        # 生成流式响应
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

                    # 累积完整文本
                    self.full_text += text_content
                    
                    # 提取引用
                    self.sources = self._extract_content_ref(self.full_text)
                    
                    # 生成当前chunk
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
        
        # 处理参考出处（如果有）
        if self.sources and hasattr(self, 'knowledge_data') and self.knowledge_data:
            # 收集所有相关引用
            references = []
            seen_references = set()
            
            for k in self.knowledge_data:
                if k['url'] in self.sources and k.get('reference'):
                    ref_items = k['reference'].split('\n')
                    for ref in ref_items:
                        ref = ref.strip()
                        if ref and ref not in seen_references:
                            seen_references.add(ref)
                            references.append(ref)
            
            # 如果有引用，生成参考出处chunk
            if references:
                self.supp_text = "\n\n**参考出处**\n\n" + "\n\n".join(references)
                delta = {"content": self.supp_text}
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

        # 模式1: 匹配 [来源: [内容1](链接1), [内容2](链接2), ...] 格式
        pattern1 = r'\[来源:\s*((?:\[[^\]]+\]\([^)]+\),?\s*)+)(?:\+more\]|\])'
        matches1 = re.findall(pattern1, full_text)
        
        # 提取单个引用内容
        for match_group in matches1:
            # 匹配每个 [内容](链接) 对
            single_refs = re.findall(r'\[([^\]]+)\]\([^)]+\)', match_group)
            for ref in single_refs:
                if ref not in seen:
                    seen.add(ref)
                    result.append(ref)
        
        # 模式2: 匹配 [来源: [内容]] 格式
        pattern2 = r'\[来源:\s*\[([^\]]+)\]\]'
        matches2 = re.findall(pattern2, full_text)
        for ref in matches2:
            if ref not in seen:
                seen.add(ref)
                result.append(ref)
        
        # 模式3: 匹配 doc_xxxx 或 graph_chunk 等直接引用
        pattern3 = r'(doc_\d+|graph_chunk|graph_\d+|data_\d+)'
        matches3 = re.findall(pattern3, full_text)
        for ref in matches3:
            if ref not in seen:
                seen.add(ref)
                result.append(ref)

        return result