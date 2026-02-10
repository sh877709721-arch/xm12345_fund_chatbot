import json
from enum import Enum
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from typing import List, Optional, Any
from uuid import uuid4
import time
import logging
import json
from starlette.background import BackgroundTask
from fastapi.responses import StreamingResponse
from app.service.chat import save_observation_message, update_chat_message, update_chat_message_background, save_observation_message_background
from app.core.graph.query_graphrag import rag_chatbot_local_search_stream
from collections import deque
# 避免循环导入：在函数内部动态导入
from app.model.message_context import ContextType


def determine_context_type(chunk_data: dict) -> ContextType:
    """
    根据 chunk 数据确定对应的 ContextType

    Args:
        chunk_data: 流式响应中的 chunk 数据字典

    Returns:
        对应的 ContextType 枚举值
    """
    if not isinstance(chunk_data, dict):
        chunk_data = {}

    object_type = chunk_data.get("object", "")

    # 根据不同的 object 类型映射到相应的 ContextType
    if object_type == "chat.completion.question":
        return ContextType.question
    elif object_type == "chat.completion.observation":
        return ContextType.observation
    elif object_type == "chat.completion.thought":
        return ContextType.thought
    elif object_type == "chat.completion.action":
        return ContextType.action
    elif object_type == "chat.completion.summary":
        return ContextType.summary
    else:
        # 默认为 observation 类型
        return ContextType.observation


def create_context_chunk(object_type: str, content: Any, model: str | None = None, **kwargs) -> dict:
    """
    创建标准化的上下文 chunk

    Args:
        object_type: 对象类型 (question, observation, thought, action, summary)
        content: 内容数据
        model: 模型名称
        **kwargs: 额外的参数

    Returns:
        标准化的 chunk 字典
    """
    chunk_id = f"chatcmpl-{uuid4().hex}"

    base_chunk = {
        "id": chunk_id,
        "object": f"chat.completion.{object_type}",
        "created": int(time.time()),
        "model": model or f"{object_type}_model",
        **kwargs
    }

    # 根据类型处理内容格式

    base_chunk["content"] = content

    return base_chunk


def save_context_chunk_by_type(chat_id: str, 
                               chunk_data: dict | str, 
                               assistant_message_id: int=0,
                               context_type: ContextType | None = None):
    """
    根据类型保存上下文 chunk

    Args:
        chat_id: 聊天会话ID
        chunk_data: chunk 数据（可以是字典或字符串）
        context_type: 指定的上下文类型，如果不指定则自动推断
    """
    # 如果没有指定 context_type，尝试推断
    if context_type is None:
        if isinstance(chunk_data, dict):
            context_type = determine_context_type(chunk_data)
        else:
            # 默认为 observation 类型
            context_type = ContextType.observation

    # 确保 chunk_data 是字符串格式（函数期望的格式）
    if isinstance(chunk_data, dict):
        # 确保包含正确的 object 类型
        if "object" not in chunk_data:
            object_type_map = {
                ContextType.question: "chat.completion.question",
                ContextType.observation: "chat.completion.observation",
                ContextType.thought: "chat.completion.thought",
                ContextType.action: "chat.completion.action",
                ContextType.summary: "chat.completion.summary"
            }
            chunk_data["object"] = object_type_map.get(context_type, "chat.completion.observation")

        # 转换为字符串格式
        chunk_str = f"data: {json.dumps(chunk_data, ensure_ascii=False)}"
    else:
        chunk_str = chunk_data

    save_observation_message_background(chat_id, assistant_message_id,chunk_str, context_type)


def create_question_chunk(question_data: list, model: str = "similary_query") -> dict:
    """
    创建 chat.completion.question 类型的 chunk

    Args:
        question_data: 问题数据列表
        model: 模型名称

    Returns:
        标准化的 question chunk
    """
    return create_context_chunk(
        object_type="question",
        content=question_data,
        model=model
    )


def create_observation_chunk(observation_content: str | dict, model: str = "observation_model") -> dict:
    """
    创建 chat.completion.observation 类型的 chunk

    Args:
        observation_content: 观察内容
        model: 模型名称

    Returns:
        标准化的 observation chunk
    """
    return create_context_chunk(
        object_type="observation",
        content=observation_content,
        model=model
    )


def create_thought_chunk(thought_content: str, model: str = "thought_model") -> dict:
    """
    创建 chat.completion.thought 类型的 chunk

    Args:
        thought_content: 思考内容
        model: 模型名称

    Returns:
        标准化的 thought chunk
    """
    return create_context_chunk(
        object_type="thought",
        content=thought_content,
        model=model
    )


def create_action_chunk(action_content: str | dict, model: str = "action_model") -> dict:
    """
    创建 chat.completion.action 类型的 chunk

    Args:
        action_content: 动作内容
        model: 模型名称

    Returns:
        标准化的 action chunk
    """
    return create_context_chunk(
        object_type="action",
        content=action_content,
        model=model
    )


def create_summary_chunk(summary_content: str, model: str = "summary_model") -> dict:
    """
    创建 chat.completion.summary 类型的 chunk

    Args:
        summary_content: 总结内容
        model: 模型名称

    Returns:
        标准化的 summary chunk
    """
    return create_context_chunk(
        object_type="summary",
        content=summary_content,
        model=model
    )


class ClientAttachment(BaseModel):
    name: str
    contentType: str
    url: str

class ToolInvocationState(str, Enum):
    CALL = 'call'
    PARTIAL_CALL = 'partial-call'
    RESULT = 'result'

class ToolInvocation(BaseModel):
    state: ToolInvocationState
    toolCallId: str
    toolName: str
    args: Any
    result: Any


class ClientMessage(BaseModel):
    role: str
    content: str
    experimental_attachments: Optional[List[ClientAttachment]] = None
    toolInvocations: Optional[List[ToolInvocation]] = None

class ChatRequest(BaseModel):
    messages: List[ClientMessage]

def convert_to_openai_messages(messages: List[ClientMessage]) -> List[ChatCompletionMessageParam]:
    openai_messages = []

    for message in messages:
        parts = []
        tool_calls = []

        parts.append({
            'type': 'text',
            'text': message.content
        })

        if (message.experimental_attachments):
            for attachment in message.experimental_attachments:
                if (attachment.contentType.startswith('image')):
                    parts.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': attachment.url
                        }
                    })

                elif (attachment.contentType.startswith('text')):
                    parts.append({
                        'type': 'text',
                        'text': attachment.url
                    })

        if(message.toolInvocations):
            for toolInvocation in message.toolInvocations:
                tool_calls.append({
                    "id": toolInvocation.toolCallId,
                    "type": "function",
                    "function": {
                        "name": toolInvocation.toolName,
                        "arguments": json.dumps(toolInvocation.args)
                    }
                })

        tool_calls_dict = {"tool_calls": tool_calls} if tool_calls else {"tool_calls": None}

        openai_messages.append({
            "role": message.role,
            "content": parts,
            **tool_calls_dict,
        })

        if(message.toolInvocations):
            for toolInvocation in message.toolInvocations:
                tool_message = {
                    "role": "tool",
                    "tool_call_id": toolInvocation.toolCallId,
                    "content": json.dumps(toolInvocation.result),
                }

                openai_messages.append(tool_message)

    return openai_messages



def _get_similarity_questions(query: str, used_id: int = -1, top_n: int = 3) -> list:
    """
    内部函数：获取相似问题列表

    Args:
        query: 查询文本
        used_id: 排除的ID
        top_n: 返回结果数量

    Returns:
        相似问题列表
    """
    try:
        # 动态导入以避免循环依赖
        from app.core.vector import get_adaptive_similarity_threshold_with_rerank_fallback
        return get_adaptive_similarity_threshold_with_rerank_fallback(query, used_id, top_n)
    except ImportError as e:
        logging.error(f"无法导入相似度搜索函数: {e}")
        return []


def qa_stream_response(chat_id, qa_res, db, user_message_id, assistant_message_id):
    # 立即保存消息到数据库获取ID
    final_text = qa_res[0]["answer"]
    saved_message = None

    try:
        saved_message = update_chat_message(chat_id, assistant_message_id, final_text, db)
        db_id = saved_message.id if saved_message else None
        logging.info(f"Pre-saved assistant message to DB with ID: {db_id}")
    except Exception as e:
        logging.exception("Failed to pre-save assistant message: %s", e)

    def qa_stream_agent():
        if user_message_id:
            user_id_chunk = {
                "id": f"user-msg-id-{uuid4().hex}",
                "object": "chat.completion.message_id",
                "created": int(time.time()),
                "model": 'qa_model',
                "message_id": {
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                }
            }
            yield f"data: {json.dumps(user_id_chunk, ensure_ascii=False)}\n\n"

        chunk_id = f"chatcmpl-{uuid4().hex}"
        chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": 'qa_model',
                    "choices": [{
                        "index": 0,
                        "delta": {"content": final_text},
                        "finish_reason": None
                    }]
                }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": 'qa_model',
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        yield f"data: [DONE]\n\n"

    return StreamingResponse(qa_stream_agent(), media_type="text/plain")


def qa_stream_response_optimized(chat_id, query, qa_res, user_message_id, assistant_message_id):
    """
    🔧 **优化版本QA流式响应**

    优化特点：
    1. 不持有数据库连接进行流式传输
    2. 使用后台任务更新最终消息内容
    3. 减少连接池占用时间
    """
    final_text = qa_res[0]["answer"]
    used_id = qa_res[0]["id"]
    reference =  f'\n\n**参考出处**: \n\n {qa_res[0]["reference"]}' if qa_res[0]["reference"] else '' # "参考来源:"
    final_content = f"{final_text}\n\n{reference}"

    # 格式化文本为Markdown友好的换行格式
    from app.core.text_formatter import format_text_for_markdown
    final_content = format_text_for_markdown(final_content)
    observation_chunks = []  # 收集观察消息用于后台处理
    similary_query = _get_similarity_questions(query, used_id, top_n=3)
    chunk_id = f"chatcmpl-{uuid4().hex}"  # 为流式响应生成统一的 chunk ID
    # 使用新的 ContextType 封装创建 question chunk
    question_chunk = create_question_chunk(
        question_data=similary_query,
        model="similary_query"
    )

    observation_chunks.append(question_chunk)
    

    def qa_stream_agent():
        # 发送消息ID
        if user_message_id:
            user_id_chunk = {
                "id": f"user-msg-id-{uuid4().hex}",
                "object": "chat.completion.message_id",
                "created": int(time.time()),
                "model": 'qa_model',
                "message_id": {
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                }
            }
            yield f"data: {json.dumps(user_id_chunk, ensure_ascii=False)}\n\n"

        # 流式传输内容
        
        chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": 'qa_model',
            "choices": [{
                "index": 0,
                "delta": {"content": final_content},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        # 结束标记
        chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": 'qa_model',
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        yield f"data: [DONE]\n\n"

    # 🔧 **关键优化：使用后台任务更新数据库，不占用流式连接**
    def background_update():
        for chunk in observation_chunks:
            # 使用新的 ContextType 封装保存 chunk
            
            save_context_chunk_by_type(chat_id, chunk,assistant_message_id,None)  # 自动推断 ContextType

        update_chat_message_background(chat_id, assistant_message_id, content=final_content)


    return StreamingResponse(
        qa_stream_agent(),
        media_type="text/plain",
        background=BackgroundTask(background_update)
    )


def agent_stream_response(chat_id, bot, final_content, agent_messages, db, user_message_id,assistant_message_id):
    #logging.info(f'agent_message:{agent_messages}')
    def stream_agent():
        # 首先发送用户消息ID（如果存在）
        if user_message_id:
            user_id_chunk = {
                "id": f"user-msg-id-{uuid4().hex}",
                "object": "chat.completion.message_id",
                "created": int(time.time()),
                "model": 'agent_model',
                "message_id": {
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                }
            }
            yield f"data: {json.dumps(user_id_chunk, ensure_ascii=False)}\n\n"

        # 这里应该使用实际的消息而不是硬编码
        recent_chunks = deque(maxlen=3)

        # bot._run_openai_format may be a sync generator; iterate normally
        for chunk in bot._run_openai_format(agent_messages):
            # accumulate for later parsing
            recent_chunks.append(chunk)
            # yield chunk as-is to the client
            save_observation_message(chat_id, chunk, db)

            yield chunk

        # After streaming finished, try to extract the assistant's final text
        if len(recent_chunks) >= 1:
            # try to parse the last few chunks for a content field
            # prefer checking the last element that contains actual content
            parsed = ""
            try:
                # iterate from newest to oldest to find content
                for c in reversed(recent_chunks):
                    if isinstance(c, str) and c.startswith("data: "):
                        json_str = c[6:]
                        if json_str.strip() == "[DONE]":
                            continue
                        chunk_data = json.loads(json_str)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                parsed = content
                                break
                if parsed:
                    #logging.info(f'Parsed final assistant content: {parsed}')
                    final_content["text"] = parsed
            except Exception as e:
                logging.warning(f"Error parsing chunks for final content: {e}")

        # 立即保存最终消息并获取数据库ID
        text = final_content.get("text")
        if text:
            try:
                saved_message = update_chat_message(chat_id,assistant_message_id, text, db)
                db_id = saved_message.id if saved_message else None
                final_content["db_id"] = db_id
                logging.info(f"Saved assistant final message to DB with ID: {db_id}")
            except Exception as e:
                logging.exception("Failed to save assistant message: %s", e)
                final_content["db_id"] = None

        yield f"data: [DONE]\n\n"
        logging.info(f'Final content to save: {final_content.get("text")}')

    # 对于agent模式，消息保存已经在流内完成，后台任务只做验证
    def _verify_saved():
        pass

    return StreamingResponse(stream_agent(), media_type="text/plain", background=BackgroundTask(_verify_saved))


def agent_stream_response_optimized(chat_id, query, bot, agent_messages, user_message_id, assistant_message_id):
    """
    🔧 **优化版本Agent流式响应**

    优化特点：
    1. 不持有数据库连接进行流式传输
    2. 观察消息使用后台任务异步保存
    3. 最终消息使用后台任务更新
    4. 大幅减少连接池占用时间
    """
    # 🔧 **修复：将数据收集器移到外部作用域，确保后台任务可以访问**
    final_content = {"text": ""}
    observation_chunks = []  # 收集观察消息用于后台处理

    # 对于 Agent 流式响应，没有直接的 used_id，使用默认值 -1
    similary_query = _get_similarity_questions(query, used_id=-1, top_n=3)
    chunk_id = f"chatcmpl-{uuid4().hex}"  # 为流式响应生成统一的 chunk ID
    # 使用新的 ContextType 封装创建 question chunk
    question_chunk = create_question_chunk(
        question_data=similary_query,
        model="similary_query"
    )

    observation_chunks.append(question_chunk)

    def stream_agent():
        # 发送消息ID
        if user_message_id:
            user_id_chunk = {
                "id": f"user-msg-id-{uuid4().hex}",
                "object": "chat.completion.message_id",
                "created": int(time.time()),
                "model": 'agent_model',
                "message_id": {
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                }
            }
            yield f"data: {json.dumps(user_id_chunk, ensure_ascii=False)}\n\n"

        # 收集流式数据用于最终内容解析
        recent_chunks = deque(maxlen=3)

        # 🔧 **关键优化：流式传输期间不进行数据库操作**
        for chunk in bot._run_openai_format(agent_messages):
            recent_chunks.append(chunk)

            # 收集观察消息类型的数据，留待后台处理
            if chunk.startswith("data: "):
                try:
                    json_str = chunk[6:].strip()
                    if json_str != "[DONE]":
                        chunk_data = json.loads(json_str)
                        if chunk_data.get("object") == "chat.completion.observation":
                            observation_chunks.append(chunk)
                except json.JSONDecodeError:
                    pass  # 忽略解析错误，继续流式传输

            # 立即向客户端发送数据
            yield chunk

        # 解析最终消息内容
        parsed_content = ""
        if len(recent_chunks) >= 1:
            try:
                for c in reversed(recent_chunks):
                    if isinstance(c, str) and c.startswith("data: "):
                        json_str = c[6:]
                        if json_str.strip() == "[DONE]":
                            continue
                        chunk_data = json.loads(json_str)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                parsed_content = content
                                break
                if parsed_content:
                    #logging.info(f'Parsed final assistant content: {parsed_content}')
                    final_content["text"] = parsed_content
            except Exception as e:
                logging.warning(f"Error parsing chunks for final content: {e}")
        
        yield f"data: [DONE]\n\n"
        # logging.info(f'Final content extracted: {final_content.get("text")}')

    # 🔧 **关键优化：使用后台任务处理所有数据库操作**
    def background_update():
        # 1. 异步保存观察消息 - 根据类型分类处理
        for chunk in observation_chunks:
            context_type = determine_context_type(chunk)
            save_context_chunk_by_type(chat_id,chunk,assistant_message_id,context_type)
            #save_observation_message_background(chat_id, chunk, context_type)

        # 2. 更新最终消息内容
        final_text = final_content.get("text")
        if final_text:
            logging.info(f'Background update: saving final message content (length: {len(final_text)})')
            update_chat_message_background(chat_id, assistant_message_id, final_text)
        else:
            logging.warning('Background update: no final text to save')

    return StreamingResponse(
        stream_agent(),
        media_type="text/plain",
        background=BackgroundTask(background_update)
    )




def graphrag_stream_response_optimized(chat_id, query, user_message_id, assistant_message_id):
    """
    🔧 **优化版本GraphRAG流式响应**

    遵循与 agent_stream_response_optimized 相同的设计模式和消息格式

    优化特点：
    1. 不持有数据库连接进行流式传输
    2. 最终消息使用后台任务更新
    3. 与agent响应格式完全一致
    4. 大幅减少连接池占用时间
    """

    # 🔧 **修复：将数据收集器移到外部作用域，确保后台任务可以访问**
    final_content = {"text": ""}

    async def stream_graphrag():
        # 发送消息ID - 与 agent_stream_response_optimized 格式一致
        if user_message_id:
            user_id_chunk = {
                "id": f"user-msg-id-{uuid4().hex}",
                "object": "chat.completion.message_id",
                "created": int(time.time()),
                "model": 'graphrag_model',
                "message_id": {
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                }
            }
            yield f"data: {json.dumps(user_id_chunk, ensure_ascii=False)}\n\n"

        start_chunk = {
            "id": f"chatcmpl-{uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "graphrag-boost",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": "正在为您检索数据...."
                    },
                    "finish_reason": None
                }
            ]
        }

        chunk_str = f"data: {json.dumps(start_chunk, ensure_ascii=False)}\n\n"
        yield chunk_str

        # 收集流式数据用于最终内容解析
        recent_chunks = deque(maxlen=3)
        accumulated_content = ""

        # 🔧 **关键优化：流式传输期间不进行数据库操作**
        try:
            # 执行 GraphRAG 本地搜索流式查询 rag_chatbot_local_search_stream
            async for chunk in rag_chatbot_local_search_stream(query):
                if chunk:  # 确保不为空
                    accumulated_content += chunk

                    # 构造标准的 OpenAI 格式响应块
                    response_chunk = {
                        "id": f"chatcmpl-{uuid4().hex}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "graphrag-boost",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "content": accumulated_content
                                },
                                "finish_reason": None
                            }
                        ]
                    }

                    chunk_str = f"data: {json.dumps(response_chunk, ensure_ascii=False)}\n\n"
                    recent_chunks.append(chunk_str)

                    # 立即向客户端发送数据
                    yield chunk_str

        except Exception as e:
            logging.error(f"GraphRAG 流式查询错误: {str(e)}")
            # 发送错误块
            error_chunk = {
                "id": f"chatcmpl-{uuid4().hex}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "graphrag-boost",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": f"GraphRAG 处理失败: {str(e)}"
                        },
                        "finish_reason": "error"
                    }
                ]
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

        # 解析最终消息内容
        parsed_content = accumulated_content  # GraphRAG 直接累积内容
        if parsed_content:
            final_content["text"] = parsed_content

        # 发送完成标记
        done_chunk = {
            "id": f"chatcmpl-{uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "graphrag-boost",
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
        yield f"data: [DONE]\n\n"

        logging.info(f"GraphRAG 流式响应完成，chat_id: {chat_id}, query: {query[:50]}..., 响应长度: {len(parsed_content)} 字符")

    # 🔧 **关键优化：使用后台任务处理所有数据库操作**
    def background_update():
        # 更新最终消息内容
        final_text = final_content.get("text")
        if final_text:
            logging.info(f'GraphRAG Background update: saving final message content (length: {len(final_text)})')
            update_chat_message_background(chat_id, assistant_message_id, final_text)
        else:
            logging.warning('GraphRAG Background update: no final text to save')

    return StreamingResponse(
        stream_graphrag(),
        media_type="text/plain",
        background=BackgroundTask(background_update)
    )


def test_context_type_functions():
    """
    测试新的 ContextType 封装功能
    """
    print("🧪 测试 ContextType 封装功能")

    # 测试不同类型的 chunk 创建
    test_cases = [
        ("question", [{"id": 1, "question": "测试问题", "answer": "测试答案"}]),
        ("observation", "这是观察内容"),
        ("thought", "这是思考过程"),
        ("action", {"action": "search", "params": {"query": "test"}}),
        ("summary", "这是对话总结")
    ]

    for obj_type, content in test_cases:
        chunk = create_context_chunk(obj_type, content, model=f"test_{obj_type}")
        print(f"✅ {obj_type} chunk 创建成功: {chunk['object']}")

        # 测试类型推断
        inferred_type = determine_context_type(chunk)
        expected_type = getattr(ContextType, obj_type)
        assert inferred_type == expected_type, f"类型推断错误: {inferred_type} != {expected_type}"
        print(f"  ✅ 类型推断正确: {inferred_type}")

    print("\n🎉 所有 ContextType 封装功能测试通过！")

    # 返回一个示例 question chunk
    sample_question_data = [
        {"id": 1, "question": "AI是什么？", "answer": "人工智能是模拟人类智能的技术。"},
        {"id": 2, "question": "机器学习原理？", "answer": "机器学习通过数据训练模型来做出预测。"}
    ]

    return create_question_chunk(sample_question_data, "qa_model")