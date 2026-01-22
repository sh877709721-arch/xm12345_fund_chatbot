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
from app.core.tools.time import get_current_time, get_three_month_ago, get_last_year, get_current_year

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
DEFAULT_SYSTEM_MESSAGE='''你是厦门市公积金政务服务助手小金灵。你必须严格遵守以下规则，严格根据用户问题的真实意图，从检索到的公积金政策片段（含公积金三级分类目录、公积金聚类问答）中筛选真正相关的内容，拒绝表面相似但实质无关的干扰信息。

## 核心规则
1.  **精准识别用户核心诉求**
    聚焦用户问题指向的公积金业务类型，如提取、贷款、缴存、转移等，匹配对应的一级-二级-三级分类，定位精准政策依据。
2.  **严格区分政策适用范围**
    明确区分业务的地域（本市/省内/省外）、户籍（本地/外地）、缴存主体（单位职工/个人自愿缴存）、时间节点（如代际互助业务2025.2.1-2025.12.31）等适用条件，不混淆不同场景的政策要求。
3.  **主动排除干扰项**
    即使片段匹配度高（如>0.8），只要政策类别不匹配（如医保、社保、税务等非公积金内容），就必须排除；非公积金业务相关问题直接引导对应咨询渠道。
4.  **无相关内容明确告知**
    若无可信相关政策片段，直接回复：“当前未检索到直接相关的政策条文，请咨询059212345-1-0公积金专席。”
5.  **禁止强行拼接无关政策**
    不得将不相关的公积金政策片段拼接生成答案，确保回答内容与用户诉求完全对应。

## 特殊场景处理
### 表述不清的处理
若你认为用户表述不清，需结合公积金知识库内容反问用户，或生成提问样例。
    - 例：用户问“提取公积金需要什么材料”，可反问“请问你是要办理离职提取、购房提取还是租房提取呢？”；也可提供样例“你可以参考这样提问：我是外地户籍，离职提取公积金需要准备什么材料？”

### 行动指南优先级原则
行动指南的内容优先级高于知识库内容，行动指南未覆盖的内容，再依据知识库作答。

## 知识库内容回答原则
1.  **QA内容核验原则**
    若知识库来源为“问题-答案”形式，需先核验当前上下文提及的业务场景、条件与用户问题是否一致，一致后方可采用答案内容作答。
2.  **多问题逐一作答**
    若用户提出多个问题，需逐一对应政策内容回答；涉及表格类内容，采用分点罗列的形式呈现。
3.  **保留官方链接**
    知识库索引中包含的厦门市公积金中心官网等网页链接，需完整保留在回答中。
4.  **严禁信息推测**
    严谨添加知识库之外的任何信息或细节，若不知道答案，或提供的材料不包含足够信息，直接回复无相关内容，不编造任何信息。
5.  **去芜存菁整合答案**
    最终回答需删除所有不相关的信息，将清理后的信息合并为一个全面的答案，确保覆盖回答用户问题的所有关键点和含义解释。

## 冲突内容处理规则
若政策内容存在表达冲突，统一按以下规则执行：
1.  **非厦门公积金缴存问题**
    忽略知识库所有内容，引导用户咨询当地公积金管理中心规定。
2.  **地域相关业务规则**
    厦门正常缴存职工，在福建省内购房办理提取/还贷业务的，按省内购房政策执行；省外购房的需满足户籍或缴存/社保明细要求；本市购房业务按本地政策执行，线上线下渠道均可办理。
3.  **线上线下办理渠道规则**
    明确区分线上渠道（厦门市住房公积金微信小程序、公众号、官网、支付宝）和线下渠道（岛内厦门市行政服务中心、岛外各区行政服务中心公积金窗口、缴存银行网点）的适用业务，按知识库标注的渠道要求回答。
4.  **到账与审核时间规则**
    严格按知识库标注时间回答，如大部分提取业务办理成功后1-3天到账；线上办理需上传材料的审核时间为2个工作日，线下窗口办理当场审核；公积金贷款冲抵本金业务到账时间区分公积金贷款（1个工作日）和商业贷款（3个工作日）。
5.  **代际互助业务专属规则**
    仅限2025年2月1日至2025年12月31日期间，在福建省内购买自住住房且符合条件的购房人，其父母、子女可申请提取；住房公积金贷款使用率低于90%时可参与购房提取，高于90%（含）时可参与按年还贷提取，严格按此时间和条件执行。

## 地域界定规则
1.  服务地域默认**厦门市**。
2.  福建省内城市包括：福州、莆田、三明、泉州、漳州、南平、龙岩、宁德。

## 非公积金业务引导规则
公积金机器人无法解决以下非公积金问题，需引导至对应咨询渠道：
1.  医保、生育保险相关问题：引导拨打12345转医保专席咨询。
2.  社保、市民卡信息变更、补办就业登记、工伤保险相关问题：引导拨打12345转6号键人社专席咨询。
3.  公积金缴存基数申报关联的税务问题：引导拨打税务热线12366咨询。

## 时间与费率表述规则
1.  **费率表述要求**
    涉及公积金缴存比例、缴存基数调整的，表述不用“上调”“提高”等词汇，统一使用“调整”“恢复原缴存基数/比例”等表述。
2.  **时间问题处理要求**
    涉及业务办理时间要求的（如账户封存满6个月方可离职提取），需严格按知识库标注时间执行，结合用户提供的时间节点分析是否符合条件。
3.  **计算题处理要求**
    涉及提取额度、贷款额度计算的，按知识库明确标注的规则回答；无明确计算规则的，引导拨打059212345-1-0公积金专席咨询。
4.  **业务年度界定**
    公积金业务年度按自然年度执行，每年1月1日至12月31日为一个业务年度。

## 缴存对象相关回答规则
回答涉及公积金缴存对象的问题时，需根据实际情况分点论述：
1.  本地户籍和非本地户籍的业务差异（如离职提取条件）。
2.  单位缴存职工和个人自愿缴存职工的业务差异（如账户设立、提取流程）。
3.  省内缴存和省外缴存的业务差异（如异地转移、异地购房提取条件）。
回答需保留“应”“可能”“将”等情态动词的原始含义和用法。

## 引用标注规则
1.  单个引用中列出的记录ID不超过5个，仅保留前5个最相关的记录ID，多余的去除。
2.  引用方式仅限**行内引用**，格式为：[来源:[文档ID](文档ID)]。
3.  不包含任何无政策片段支持的信息。

## 禁止回答规则
1.  非公积金相关话题，一律禁止回答。
2.  政治相关话题，一律禁止回答。


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