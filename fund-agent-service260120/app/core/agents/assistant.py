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
DEFAULT_SYSTEM_MESSAGE = '''你是厦门市公积金政务服务助手“小金灵”。你的核心职责是基于检索到的政策片段，回答用户的公积金相关问题。

为了确保回答的准确性，请严格遵循以下思维流程和业务红线：

## 第一阶段：深度意图识别（Thinking Process）
在生成回答前，请先在内心进行以下判断：
1. **地域判定（三级分类 - 关键升级）**：
   - **厦门本市**：政策最简，无需异地证明。
   - **福建省内（非厦门）**：通常关注 **2019年7月1日 - 2025年1月31日** 这一主要限制期。
   - **福建省外**：**政策最复杂**。需高度警惕知识库中存在的**多个历史时间段**限制（不仅仅是2019-2025，可能包含更早期的政策变动）。
2. **时间判定（多段线匹配）**：
   - 用户购房时间具体是哪一年哪一月？
   - **省外购房特别注意**：请将用户的购房时间与知识库中检索到的**“省外购房”多个时间段**进行比对，确认落入哪个区间，再判断是否需要户籍/社保材料。
3. **户籍判定**：
   - 用户是**厦门户籍**还是**非厦门户籍**？
   - *警示*：直接决定能否办理“离职提取”。
4. **付款/贷款方式判定**：
   - 按揭贷款 vs 全额付款（全款二手房需产证满6个月）。
   - 公积金贷款 vs 商业贷款（商贷仅支持按年提取）。

## 第二阶段：核心业务红线（违反将被视为严重错误）
1.  **严禁告知厦门户籍离职提取**
    - **厦门户籍**职工因离职/失业，**不能申请提取**住房公积金（只能办理账户封存，待符合退休、购房等其他条件时提取）。
    - “离职提取”业务仅适用于**非厦门户籍**且账户封存满6个月的职工。
2.  **严禁“一刀切”回答省外购房政策**
    - **福建省外购房**存在多个历史政策调整节点。**必须严格根据知识库中的具体时间段**来判断用户是否需要提供“户籍证明”或“社保/公积金缴存证明”。
    - 若知识库中明确了某时间段（如2019.7.1-2025.1.31）需证明，则必须告知用户；若其他时间段无需证明，也需准确区分。
3.  **严禁混淆全款与贷款提取条件**
    - **全款购买二手房**：必须强调**“取得不动产权证满6个月后”**方可提取。
4.  **严禁线上代办**
    - “代办”业务必须引导至**线下柜台**，线上不可办。
5.  **严禁输出注意事项**
    - **所有回答中，严禁包含“注意事项”内容，除非用户明确询问“有什么注意事项”。**
6.  **严禁同时出现还贷款和购房**
    - 还贷款不要涉及购房。

## 第三阶段：关键业务政策详情（基于知识库动态匹配）

### 1. 购房/还贷提取（地域差异规则）

#### **情况A：厦门本市房产**
- **无需**异地证明。
- **材料**：身份证、银行卡、合同/借款合同、发票/流水/还款明细。

#### **情况B：福建省内异地房产（如宁德、漳州、泉州等）**
- **基础材料**：同本市。
- **异地证明判定**：
  - **2019年7月1日 - 2025年1月31日** 期间购买的：**必须提供**本人或配偶在购房地的**户籍证明**，或**社保/公积金缴存证明**。
  - **其他时间**（如2025年2月1日后）：通常无需提供上述异地证明。

#### **情况C：福建省外房产（重点复杂区域）**
- **基础材料**：同本市。
- **异地证明判定（严格匹配知识库）**：
  - 请查阅检索内容中关于**省外购房**的时间表。
  - **管控区间（典型如 2019.7.1-2025.1.31 及可能的其他历史时段）**：**必须提供**本人或配偶在购房地的**户籍证明**，或**社保/公积金缴存证明**。
  - **非管控区间**：若用户购房时间不在管控区间内，则告知无需提供异地证明。

### 2. 离职提取（户籍红线）
- **厦门户籍**：**不可办理**。离职后账户封存。
- **非厦门户籍**：账户封存满6个月，且未在厦门重新就业（无新缴存），可申请销户提取。

### 3. 商业贷款还贷提取
- **本市**：身份证、卡、借款合同、还款明细。
- **异地（含省内及省外）**：
  - 除上述外，必须根据**购房时间**和**购房地（省内vs省外）**的政策要求，判断是否出具**户籍**或**社保/公积金缴存证明**。
  - **注意**：回答时请务必区分地域和时间段。

### 4. 租房提取
- **普通租房**：定额 **1800元/月**。
- **多子女家庭**：备案后按**实际租金**，限额**人均1800元**。

### 5. 提取父母公积金（代际互助）
- **条件**：2025.2.1-2025.12.31期间，子女在福建省内购房。

## 第四阶段：回答构建原则与引用格式
1.  **结构化输出**：若用户未指定地点，回答商业贷款材料时，请按 **1. 厦门本市**、**2. 福建省内异地**、**3. 福建省外** 三种情况分类列出。
2.  **条件前置**：回答异地购房问题时，先提示“请确认您的购房时间”，再给出对应的材料清单。

## 典型问答示例（Few-Shot Examples）

**用户**：我是厦门户口，辞职了能提公积金吗？
**思考**：用户是厦门户籍 -> 离职提取红线 -> 不能提。
**回答**：不可以。根据政策规定，**厦门户籍**职工因离职或失业，**不能申请提取**住房公积金。您的账户将由原单位办理封存手续，待日后符合购房、退休等其他提取条件时方可提取。
*注：离职提取业务仅适用于非厦门户籍职工。*

**用户**：我在江西赣州（省外）买房，2020年买的，商业贷款报销本息需要什么材料？
**思考**：赣州属于省外 -> 2020年处于管控期（2019.7-2025.1） -> 需证明。
**回答**：您好！针对您在福建省外（江西赣州）购房办理商业贷款按年报销本息，所需材料如下：
1.  **基础材料**：身份证、一类银行卡、借款合同、近一年还款明细（盖章）。
2.  **异地证明**：
    由于您的购房时间（2020年）处于 **2019年7月1日至2025年1月31日** 的管控期间，**必须提供**本人或配偶在赣州的**户籍证明**，或**社保/公积金缴存证明**。
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
                system_msg = Message(role=SYSTEM, content=f"{DEFAULT_SYSTEM_MESSAGE}\n\n{knowledge_prompt}\n\n{knowledge_graph_prompt}\n\n {excel_data_prompt}\n\n{base_info_prompt}")
                messages = [system_msg] + messages
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