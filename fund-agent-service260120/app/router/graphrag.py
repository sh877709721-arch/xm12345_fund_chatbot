"""
GraphRAG 聊天路由

遵循 SOLID 原则：
- S: 单一职责，专门处理 GraphRAG 查询
- O: 开放封闭，可扩展新的查询类型
- L: 里氏替换，接口一致
- I: 接口隔离，功能专一
- D: 依赖倒置，依赖抽象而非具体实现
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, AsyncGenerator
import json
import logging
from app.core.graph.query_graphrag import rag_chatbot_global_search, rag_chatbot_stream, rag_chatbot_local_search, rag_chatbot_local_search_stream
from app.core.graph.sync_graphrag import rag_chatbot_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graphrag", tags=["GraphRAG"])


class GraphRAGQuery(BaseModel):
    query: str
    use_sync: Optional[bool] = False  # 是否使用同步版本


class GraphRAGResponse(BaseModel):
    response: str
    success: bool
    metadata: Optional[Dict[str, Any]] = None


class GraphRAGStreamQuery(BaseModel):
    query: str
    # 流式查询的额外参数
    community_level: Optional[int] = 2
    dynamic_community_selection: Optional[bool] = False
    response_type: Optional[str] = "Multiple Paragraphs"


class LocalSearchQuery(BaseModel):
    query: str
    # 本地搜索的额外参数
    community_level: Optional[int] = 2
    response_type: Optional[str] = "Multiple Paragraphs"


class LocalSearchStreamQuery(BaseModel):
    query: str
    # 本地搜索流式查询的额外参数
    community_level: Optional[int] = 2
    response_type: Optional[str] = "Multiple Paragraphs"


@router.post("/query", response_model=GraphRAGResponse)
async def graphrag_query(
    request: GraphRAGQuery,
    background_tasks: BackgroundTasks
) -> GraphRAGResponse:
    """
    GraphRAG 查询端点

    KISS原则：简单直接的接口设计
    YAGNI原则：只实现必要的功能
    """
    try:
        logger.info(f"收到 GraphRAG 查询: {request.query[:50]}...")

        if request.use_sync:
            # 使用同步版本（适用于特殊情况）
            response = rag_chatbot_sync(request.query)
        else:
            # 使用异步版本（推荐方式）
            response = await rag_chatbot_global_search(request.query)

        logger.info("GraphRAG 查询成功完成")

        return GraphRAGResponse(
            response=response,
            success=True,
            metadata={
                "query_length": len(request.query),
                "response_length": len(response),
                "sync_mode": request.use_sync
            }
        )

    except Exception as e:
        logger.error(f"GraphRAG 查询失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG 查询处理失败: {str(e)}"
        )


@router.post("/query/stream")
async def graphrag_stream_query(
    request: GraphRAGStreamQuery
) -> StreamingResponse:
    """
    GraphRAG 流式查询端点

    KISS原则：简单直接的流式接口
    YAGNI原则：只实现必要的流式功能

    返回 Server-Sent Events (SSE) 格式的流式响应
    """
    try:
        logger.info(f"收到 GraphRAG 流式查询: {request.query[:50]}...")

        async def generate_stream() -> AsyncGenerator[str, None]:
            """
            生成流式响应的异步生成器

            返回格式为 Server-Sent Events:
            data: {"type": "chunk", "content": "..."}
            data: {"type": "done", "content": ""}
            """
            try:
                # 发送开始信号
                yield f"data: {json.dumps({'type': 'start', 'query': request.query})}\n\n"

                # 处理流式响应
                async for chunk in rag_chatbot_stream(request.query):
                    if chunk:  # 确保不为空
                        # 发送数据块
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                # 发送完成信号
                yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

                logger.info(f"GraphRAG 流式查询完成: {request.query[:50]}...")

            except Exception as e:
                logger.error(f"流式查询处理失败: {str(e)}")
                # 发送错误信号
                error_data = {
                    'type': 'error',
                    'content': f'流式查询处理失败: {str(e)}'
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )

    except Exception as e:
        logger.error(f"GraphRAG 流式查询初始化失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG 流式查询初始化失败: {str(e)}"
        )


@router.post("/local-search", response_model=GraphRAGResponse)
async def local_search_query(
    request: LocalSearchQuery,
    background_tasks: BackgroundTasks
) -> GraphRAGResponse:
    """
    GraphRAG 本地搜索查询端点

    本地搜索适合精确查询特定实体和关系的场景

    KISS原则：简单直接的本地搜索接口
    YAGNI原则：只实现必要的本地搜索功能
    """
    try:
        logger.info(f"收到 GraphRAG 本地搜索查询: {request.query[:50]}...")

        # 执行本地搜索
        response = await rag_chatbot_local_search(request.query)

        logger.info("GraphRAG 本地搜索查询成功完成")

        return GraphRAGResponse(
            response=response,
            success=True,
            metadata={
                "query_length": len(request.query),
                "response_length": len(response),
                "search_type": "local",
                "community_level": request.community_level,
                "response_type": request.response_type
            }
        )

    except Exception as e:
        logger.error(f"GraphRAG 本地搜索查询失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG 本地搜索查询处理失败: {str(e)}"
        )


@router.post("/local-search/stream")
async def local_search_stream_query(
    request: LocalSearchStreamQuery
) -> StreamingResponse:
    """
    GraphRAG 本地搜索流式查询端点

    本地搜索流式查询，适合精确查询场景的实时响应

    KISS原则：简单直接的本地搜索流式接口
    YAGNI原则：只实现必要的本地搜索流式功能

    返回 Server-Sent Events (SSE) 格式的流式响应
    """
    try:
        logger.info(f"收到 GraphRAG 本地搜索流式查询: {request.query[:50]}...")

        async def generate_local_stream() -> AsyncGenerator[str, None]:
            """
            生成本地搜索流式响应的异步生成器

            返回格式为 Server-Sent Events:
            data: {"type": "start", "query": "..."}
            data: {"type": "chunk", "content": "..."}
            data: {"type": "done", "content": ""}
            """
            try:
                # 发送开始信号
                yield f"data: {json.dumps({'type': 'start', 'query': request.query, 'search_type': 'local'})}\n\n"

                # 处理本地搜索流式响应
                full_text = ""
                async for chunk in rag_chatbot_local_search_stream(request.query):
                    if chunk:  # 确保不为空
                        # 发送数据块
                        full_text+=chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': full_text})}\n\n"

                # 发送完成信号
                yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

                logger.info(f"GraphRAG 本地搜索流式查询完成: {request.query[:50]}...")

            except Exception as e:
                logger.error(f"本地搜索流式查询处理失败: {str(e)}")
                # 发送错误信号
                error_data = {
                    'type': 'error',
                    'content': f'本地搜索流式查询处理失败: {str(e)}'
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate_local_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )

    except Exception as e:
        logger.error(f"GraphRAG 本地搜索流式查询初始化失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG 本地搜索流式查询初始化失败: {str(e)}"
        )


@router.get("/health")
async def graphrag_health() -> Dict[str, Any]:
    """GraphRAG 服务健康检查"""
    return {
        "status": "healthy",
        "service": "GraphRAG",
        "async_available": True,
        "sync_available": True,
        "stream_available": True,
        "local_search_available": True,
        "local_search_stream_available": True
    }