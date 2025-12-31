# Copyright 2023 The Qwen team, Alibaba Group. All rights reserved.
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

import json
from typing import Dict, Iterator, List, Literal, Optional, Tuple, Union

from qwen_agent.agents.fncall_agent import FnCallAgent
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import ASSISTANT, DEFAULT_SYSTEM_MESSAGE, Message
from qwen_agent.settings import MAX_LLM_CALL_PER_RUN
from qwen_agent.tools import BaseTool
from qwen_agent.utils.utils import format_as_text_message, merge_generate_cfgs
import time
import re
from uuid import uuid4
import logging

TOOL_DESC = (
    '{name_for_model}: Call this tool to interact with the {name_for_human} API. '
    'What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters} {args_format}')

PROMPT_REACT = """Answer the following questions as best you can. You have access to the following tools:

{tool_descs}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
Restrictions: The final response should be phrased as if answering a customer service inquiry, without any code-prefixed additions

Begin!

Question: {query}
Thought: """


class ReActChat(FnCallAgent):
    """This agent use ReAct format to call tools"""

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None,
                 **kwargs):
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message=system_message,
                         name=name,
                         description=description,
                         files=files,
                         **kwargs)
        self.extra_generate_cfg = merge_generate_cfgs(
            base_generate_cfg=self.extra_generate_cfg,
            new_generate_cfg={'stop': ['Observation:', 'Observation:\n']},
        )

    def _sanitize_stream_text(self, text: str) -> str:
        """Remove internal control tokens (e.g. leading 'Thought:' / 'Final Answer:')
        from streamed deltas so the client doesn't see internal reasoning markers.
        This only strips common leading patterns, leaving the rest untouched.
        """
        # Remove the combined pattern: 'Thought: I now know the final answer\nFinal Answer:'
        text = re.sub(r"^\s*Thought:\s*I now know the final answer\s*\n\s*Final Answer:\s*", "", text, flags=re.IGNORECASE)
        #Remove generic leading 'Thought:' or 'Final Answer:' tokens
        text = re.sub(r"^\s*Thought:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^\s*Final Answer:\s*", "\n", text, flags=re.IGNORECASE)
        return text

    def _run(self, messages: List[Message], lang: Literal['en', 'zh'] = 'en', **kwargs) -> Iterator[List[Message]]:
        text_messages = self._prepend_react_prompt(messages, lang=lang)

        num_llm_calls_available = MAX_LLM_CALL_PER_RUN
        response: str = 'Thought: '
        while num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            # Display the streaming response (sanitize what is sent to the client)
            output = []
            for output in self._call_llm(messages=text_messages):
                if output:
                    delta = output[-1].content
                    # Only sanitize when delta is a string (typical case). Leave other types untouched.
                    if isinstance(delta, str):
                        display_delta = self._sanitize_stream_text(delta)
                    else:
                        display_delta = delta
                    yield [Message(role=ASSISTANT, content=response + display_delta)]

            # Accumulate the current response (keep original content for internal use)
            if output:
                response += output[-1].content

            has_action, action, action_input, thought = self._detect_tool(output[-1].content)
            if not has_action:
                break

            # Add the tool result
            observation = self._call_tool(action, action_input, messages=messages, **kwargs)
            observation = f'\nObservation: {observation}\nThought: '
            response += observation
            yield [Message(role=ASSISTANT, content=response)]

            if (not text_messages[-1].content.endswith('\nThought: ')) and (not thought.startswith('\n')):
                # Add the '\n' between '\nQuestion:' and the first 'Thought:'
                text_messages[-1].content += '\n'
            if action_input.startswith('```'):
                # Add a newline for proper markdown rendering of code
                action_input = '\n' + action_input
            text_messages[-1].content += thought + f'\nAction: {action}\nAction Input: {action_input}' + observation

    def _prepend_react_prompt(self, messages: List[Message], lang: Literal['en', 'zh']) -> List[Message]:
        tool_descs = []
        for f in self.function_map.values():
            function = f.function
            name = function.get('name', None)
            name_for_human = function.get('name_for_human', name)
            name_for_model = function.get('name_for_model', name)
            assert name_for_human and name_for_model
            args_format = function.get('args_format', '')
            tool_descs.append(
                TOOL_DESC.format(name_for_human=name_for_human,
                                 name_for_model=name_for_model,
                                 description_for_model=function['description'],
                                 parameters=json.dumps(function['parameters'], ensure_ascii=False),
                                 args_format=args_format).rstrip())
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool.name for tool in self.function_map.values())
        text_messages = [format_as_text_message(m, add_upload_info=True, lang=lang) for m in messages]
        text_messages[-1].content = PROMPT_REACT.format(
            tool_descs=tool_descs,
            tool_names=tool_names,
            query=text_messages[-1].content,
        )
        return text_messages

    def _detect_tool(self, text: str) -> Tuple[bool, str, str, str]:
        special_func_token = '\nAction:'
        special_args_token = '\nAction Input:'
        special_obs_token = '\nObservation:'
        func_name, func_args = None, None
        i = text.rfind(special_func_token)
        j = text.rfind(special_args_token)
        k = text.rfind(special_obs_token)
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                # then it is likely that `Observation` is ommited by the LLM,
                # because the output text may have discarded the stop word.
                text = text.rstrip() + special_obs_token  # Add it back.
            k = text.rfind(special_obs_token)
            func_name = text[i + len(special_func_token):j].strip()
            func_args = text[j + len(special_args_token):k].strip()
            text = text[:i]  # Return the response before tool call, i.e., `Thought`
        return (func_name is not None), func_name, func_args, text

    def _detect_stream_state_and_content(self, delta: Union[str, List]) -> Tuple[str, str, dict]:
        """
        检测流式输出的状态并清理内容
        返回: (object_type, cleaned_delta, tools_info)
        object_type:

            'chat.completion.think'
            'chat.completion.action'
            'chat.completion.chunk'

        tools_info: 包含action和action_input的字典
        """
        # 将delta转换为字符串，简化处理
        delta_str = str(delta) if not isinstance(delta, list) else ''
        if isinstance(delta, list):
            # 简化处理：直接将列表转换为字符串
            delta_str = ''.join([str(item) for item in delta])
        
        #logging.info(f"delta_str: {delta_str}")

        # 初始化tools信息
        tools_info = {}

        # 检测是否包含特殊标记
        has_action = '\nAction:' in delta_str
        has_final_answer = '\nFinal Answer:' in delta_str
        has_thought = 'Thought:' in delta_str

        # 确定当前状态 - 优先级：Action > Final Answer > Thought > 默认
        if has_action:
            object_type = 'chat.completion.action'

            # 提取Action名称
            action_match = re.search(r'\nAction:\s*([^\n]+)', delta_str)
            if action_match:
                action_name = action_match.group(1).strip()
                tools_info['action'] = action_name

            # 提取Action Input
            input_match = re.search(r'\nAction Input:\s*([^\n]+)', delta_str)
            if input_match:
                action_input = input_match.group(1).strip()
                tools_info['action_input'] = action_input
        elif has_final_answer:
            # 当同时存在Thought和Final Answer时，优先处理Final Answer
            object_type = 'chat.completion.chunk'

            # 如果同时存在Thought和Final Answer，截断Final Answer前面的内容
            if has_thought and has_final_answer:
                final_answer_pos = delta_str.find('Final Answer:')
                if final_answer_pos != -1:
                    # 提取Final Answer之后的内容
                    delta_str = delta_str[final_answer_pos + len('Final Answer:'):].strip()
                else:
                    # 备用方案：使用正则表达式提取Final Answer内容
                    final_answer_match = re.search(r'Final Answer:\s*(.*)', delta_str, re.DOTALL)
                    if final_answer_match:
                        delta_str = final_answer_match.group(1).strip()
            else:
                # 只有Final Answer，没有Thought时，移除Final Answer标记
                final_answer_match = re.search(r'Final Answer:\s*(.*)', delta_str, re.DOTALL)
                if final_answer_match:
                    delta_str = final_answer_match.group(1).strip()
        elif has_thought:
            object_type = 'chat.completion.think'
        else:
            object_type = 'chat.completion.think'

        # 清理delta内容，移除标记token
        cleaned_delta = delta_str

        # 移除各种标记
        markers_to_remove = [
            'Thought:', 'Thought',
            'Action:', 'Action',
            'Action Input:', 'Action Input',
            'Observation:', 'Observation',
            'Final Answer:', 'Final Answer',
            'I now know the final answer',  # 去除这个英文标记
            'I now know the final answer\n',
            '\nFinal'
        ]

        for marker in markers_to_remove:
            cleaned_delta = cleaned_delta.replace(marker, '')

        # 清理多余的换行和空格，但要保留有意义的内容
        cleaned_delta = cleaned_delta.strip()

        return object_type, cleaned_delta, tools_info


    def _run_openai_format(
        self,
        messages: List[Message],
        lang: Literal['en', 'zh'] = 'zh',
        **kwargs
    ) -> Iterator[str]:
        text_messages = self._prepend_react_prompt(messages, lang=lang)

        num_llm_calls_available = MAX_LLM_CALL_PER_RUN
        
        chunk_id = f"chatcmpl-{uuid4().hex}"
        created = int(time.time())
        model = "xmtelecom"

        while num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            # ---------- 1. 流式调用 LLM ----------
            llm_output = []                       # ← 改名，避免跟外层变量冲突
            for llm_output in self._call_llm(messages=text_messages):
                if llm_output:
                    delta = llm_output[-1].content

                    
                    # 检测当前状态并清理内容
                    object_type, cleaned_delta, tools_info = self._detect_stream_state_and_content(delta)
                    if not cleaned_delta:
                        continue

                    chunk = {
                        "id": chunk_id,
                        "object": object_type,
                        "created": created,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": cleaned_delta},
                            "finish_reason": None
                        }],
                        "toosls": tools_info if object_type == 'chat.completion.action' else None
                    }

                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            if not llm_output:
                break

            round_text = llm_output[-1].content
            has_action, action, action_input, thought = self._detect_tool(round_text)
            if not has_action:
                break

            # ---------- 3. 执行工具 ----------
            observation = self._call_tool(action, action_input, messages=messages, **kwargs)
            observation_text = f"\nObservation: {observation}"
            #response_content += observation_text

            # 3. 把“本轮模型输出 + 观察”追加到历史，形成新的 prompt
            text_messages[-1].content += round_text + observation_text

            # ---------- 5. 把 Observation 流式发给前端（可选） ----------
            obs_chunk  = {
                "id": chunk_id,
                "object": "chat.completion.observation",
                "created": created,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": observation_text},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(obs_chunk, ensure_ascii=False)}\n\n"

            # 更新 messages 状态（略）

        # 最终结束帧
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