from fastapi import APIRouter, HTTPException,Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.middleware.api_rate_limiter import limiter
import json
from app.service.search_service import SearchService
from app.core.agents.factory import agent_factory
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
from qwen_agent.llm.schema import Message,ContentItem
from app.service.chat import get_new_chat_instance,append_chat_message,get_chat_messages, get_recent_similary_qa,get_observation_message_context
from app.config.database import get_db
from app.core.util import qa_stream_response_optimized, agent_stream_response_optimized,graphrag_stream_response_optimized
from app.model.message import MessageRead
from app.utils.circuit_breaker import database_circuit_breaker
from app.schema.base import BaseResponse
from app.middleware.api_rate_limiter import limiter, get_rate_limit_key_by_ip
import logging


logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/chat")


def extract_message_content(content: Union[str, List[ContentItem]]) -> str:
    """从消息内容中提取文本内容，用于查询和处理"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # 提取所有文本内容并用空格连接
        text_parts = []
        for item in content:
            if item.text:
                text_parts.append(item.text)
            elif item.file:
                # 如果有文件URL，可以添加文件引用说明
                text_parts.append(f"[文件: {item.file}]")
        return " ".join(text_parts)
    else:
        return str(content)

def extract_files_from_content(content: Union[str, List[ContentItem]]) -> List[str]:
    """从消息内容中提取文件URL列表"""
    if isinstance(content, str):
        return []
    elif isinstance(content, list):
        files = []
        for item in content:
            if item.file:
                files.append(item.file)
        return files
    else:
        return []




class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None  # 历史消息, e.g. [{"role": "user", "content": "..."}]
    model: Optional[str] = "default"  # 从前端模型选择传入
    use_web_search: bool = False  # 从前端开关传入

class AssistantResponse(BaseModel):
    from_: str = "assistant"  # 固定为 assistant
    versions: List[Dict[str, str]] = [] # [{"id": "...", "content": "..."}]
    sources: Optional[List[Dict[str, str]]] = None  # [{"href": "...", "title": "..."}]
    tools: Optional[List[Dict]] = None  # [{"name": "...", "description": "...", "status": "...", "parameters": {...}, "result": "...", "error": "..."}]
    reasoning: Optional[Dict[str, Any]] = None  # {"content": "...", "duration": ...}
    avatar: str = ""  # 默认

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[ContentItem]]

class ChatRequest(BaseModel):
    chat_id: str
    model: str = 'default'
    messages: List[ChatMessage] = []
    max_tokens: int = 8192
    temperature: float = 0.2
    from_source: Optional[str] = 'web'  # 流量入口：web/miniprogram/mp/h5等

class ChatRefRequest(BaseModel):
    message_id: int
    refer_id: str

class GraphQueryRequest(BaseModel):
    query: str  # 查询文本



# API endpoint
@router.post("/completions")
@database_circuit_breaker
@limiter.limit("60/minute", key_func=get_rate_limit_key_by_ip)
def handle_chat_data(request:Request,
                     chat_request:ChatRequest, 
                     db = Depends(get_db)):

    # 从请求体中提取消息
    messages = chat_request.messages
    chat_id = chat_request.chat_id

    # guard: ensure messages provided
    if not messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    # 第一个message 为assistant，就移除第一个元素（如果存在）
    if len(messages) > 0 and messages[0].role == 'assistant':
        messages.pop(0)

    # 保存用户最近一条（使用最后一条 user message）
    user_message_id = None
    if messages and messages[-1].role == 'user':
        # 提取消息文本内容用于保存
        message_text = extract_message_content(messages[-1].content)

        # 获取流量来源（默认为 web）
        source = chat_request.from_source or 'web'

        # 记录流量来源
        logging.info(f"📊 流量来源: {source} | chat_id: {chat_id}")

        db_res = append_chat_message(chat_id,
                                     Message("user",message_text),
                                     db,
                                     meta_data={"client": source})
        saved_user_message = MessageRead.model_validate(db_res)
        user_message_id = saved_user_message.id
        messages[-1].content = [
            ContentItem(text=message_text)
            ]

    # 插入一条空的记录
    source = chat_request.from_source or 'web'
    assistant_message = append_chat_message(chat_id,
                                            Message("assistant", " "),
                                            db,
                                            meta_data={"client": source})
    assistant_message_id = assistant_message.id

    # 🔧 **优化点1：提前释放数据库连接**
    # 在流式响应开始前完成所有同步数据库操作
    query = extract_message_content(messages[-1].content)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 预先检查QA响应，此时仍持有数据库连接
    agent_messages = []
    qa_res = SearchService.qa_response(query,score=0.95,top_n=1)

    # 🔧 **优化点2：在连接释放前准备流式数据**
    for msg in messages:
        # 提取消息内容并转换为 qwen_agent 的 Message 格式
        message_text = extract_message_content(msg.content)
        agent_messages.append(Message(msg.role, message_text))

    # 🔧 **关键优化：数据库连接在此处自动释放**
    # 当函数返回StreamingResponse时，FastAPI会自动调用get_db()的finally块关闭连接
    # 流式响应将在无数据库连接的情况下进行

    if qa_res:
        logging.info(f'QA 命中了, qa_res:{qa_res},user_message_id:{user_message_id}, assistant_message_id:{assistant_message_id}')
        # 传递消息ID而不是数据库连接，流式响应将使用后台任务更新数据库
        
        return qa_stream_response_optimized(chat_id, query ,qa_res, user_message_id, assistant_message_id)

    model = chat_request.model
    bot = agent_factory.get_agent('rag_bot')
    if model=='default':
        bot = agent_factory.get_agent('rag_bot')
    elif model=='boost':
        # 使用 GraphRAG 本地搜索进行增强响应
        logging.info(f'使用 GraphRAG boost 模式处理查询: {query[:50]}...')
        return graphrag_stream_response_optimized(
            chat_id=chat_id,
            query=query,
            user_message_id=str(user_message_id) if user_message_id else "",
            assistant_message_id=str(assistant_message_id)
        )
    elif model=='guideline_bot':
        bot = agent_factory.get_agent('guideline_bot')
    
    elif model=='react_bot':
        bot = agent_factory.get_agent('react_bot')
    # agent模式也使用优化版本 #rag_bot qwen_rag_bot
    return agent_stream_response_optimized(chat_id, query, bot, agent_messages, user_message_id, assistant_message_id)






@router.post("/reset-chat-session")
def reset_chat_session(request: Request,db = Depends(get_db)):
    '''
        重置聊天会话，清空消息
    '''

     
    # 从请求中获取用户信息，如果没有则为空字符串
    user_id = getattr(request.state, 'user_id', '') if hasattr(request, 'state') else ''
    
    # 如果user_id为空，则生成guest用户ID
    chat_instance = get_new_chat_instance(user_id,db)
    return chat_instance



@router.post("/get_resent_messages", response_model=BaseResponse)
def get_recent_messages(chat_id: str,db = Depends(get_db)):
    '''
        重置聊天会话，清空消息
    '''
    messages = get_chat_messages(chat_id,db)
    return BaseResponse(data=messages)


@router.post("/get_similary_qa")
def get_similary_qa(chat_id:str, db = Depends(get_db)):
    '''
        获取最近一条相近的QA
    '''
    qa_pairs = get_recent_similary_qa(chat_id, db)
    if qa_pairs:
        return qa_pairs

    return []  # 没有数据时返回空列表




@router.post("/get_reference_content", response_model=BaseResponse[str] )
def get_reference_content(request:ChatRefRequest, 
                          db = Depends(get_db)):
    message_id = request.message_id
    refer_id = request.refer_id
    context = get_observation_message_context(message_id,db)
    if not context or not isinstance(context, dict):
        return BaseResponse(data="无法获取上下文")
    

    key = f'[文件]({refer_id})'

    try:

        refer_content = context.get(key)
        if refer_content:
            return BaseResponse(data=refer_content)
        
        key = f'[文件](doc_{refer_id})'
        refer_content = context.get(key)
        if refer_content:
            return BaseResponse(data=refer_content)

        key = f'[文件](graph_{refer_id})'
        refer_content = context.get(key)
        if refer_content:
            return BaseResponse(data=refer_content)

    except:
        return BaseResponse(data="无法获取上下文")

    