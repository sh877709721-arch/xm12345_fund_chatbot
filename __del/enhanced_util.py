"""
增强版工具模块，集成GraphRAG中间结果提取功能

基于原有 util.py 进行扩展，添加中间结果收集和可视化功能
"""

import json
import time
import logging
import uuid
from typing import List, Optional, Any, Dict, Union
from pathlib import Path

import pandas as pd
from starlette.background import BackgroundTask
from fastapi.responses import StreamingResponse

from app.core.util import (
    ClientMessage,
    ChatRequest,
    convert_to_openai_messages,
    qa_stream_response_optimized,
    update_chat_message_background,
    graphrag_stream_response_optimized
)
from app.core.graph.enhanced_query_graphrag import (
    rag_chatbot_local_search_stream_with_results,
    get_intermediate_results_summary,
    list_all_intermediate_results
)
from app.core.graph.intermediate_results import IntermediateResultsCollector


def graphrag_stream_response_with_intermediate_results(
    chat_id: str,
    query: str,
    user_message_id: str,
    assistant_message_id: str,
    enable_intermediate_collection: bool = True
) -> StreamingResponse:
    """
    增强版 GraphRAG 流式响应，支持中间结果收集

    Args:
        chat_id: 聊天ID
        query: 查询内容
        user_message_id: 用户消息ID
        assistant_message_id: 助手消息ID
        enable_intermediate_collection: 是否启用中间结果收集

    Returns:
        StreamingResponse: 流式响应对象
    """

    # 为每个查询生成唯一ID
    query_id = f"{chat_id}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

    # 数据收集器
    final_content = {"text": ""}

    async def stream_graphrag_with_results():
        # 发送消息ID
        if user_message_id:
            user_id_chunk = {
                "id": f"user-msg-id-{uuid.uuid4().hex}",
                "object": "chat.completion.message_id",
                "created": int(time.time()),
                "model": 'graphrag-enhanced',
                "message_id": {
                    "user_message_id": user_message_id,
                    "assistant_message_id": assistant_message_id,
                    "query_id": query_id  # 添加查询ID到响应中
                }
            }
            yield f"data: {json.dumps(user_id_chunk, ensure_ascii=False)}\n\n"

        # 发送开始提示
        start_chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "graphrag-enhanced",
            "choices": [{
                "index": 0,
                "delta": {"content": "🔍 正在执行智能检索并收集中间结果..."},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(start_chunk, ensure_ascii=False)}\n\n"

        accumulated_content = ""

        try:
            # 执行增强的GraphRAG搜索
            async for chunk in rag_chatbot_local_search_stream_with_results(
                query=query,
                query_id=query_id,
                collect_results=enable_intermediate_collection
            ):
                if chunk:
                    accumulated_content += chunk

                    # 构造标准的响应块
                    response_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "graphrag-enhanced",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None
                        }]
                    }

                    chunk_str = f"data: {json.dumps(response_chunk, ensure_ascii=False)}\n\n"
                    yield chunk_str

        except Exception as e:
            logging.error(f"增强GraphRAG流式查询错误: {str(e)}")

            # 发送错误信息
            error_chunk = {
                "id": f"chatcmpl-{uuid.uuid4().hex}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "graphrag-enhanced",
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"❌ 查询处理失败: {str(e)}"},
                    "finish_reason": "error"
                }]
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

        # 保存最终内容
        final_content["text"] = accumulated_content

        # 如果启用了结果收集，添加中间结果信息
        if enable_intermediate_collection:
            try:
                # 获取中间结果摘要
                summary = get_intermediate_results_summary(query_id)
                if summary:
                    # 发送中间结果摘要作为特殊chunk
                    metadata_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex}",
                        "object": "chat.completion.metadata",
                        "created": int(time.time()),
                        "model": "graphrag-enhanced",
                        "metadata": {
                            "type": "intermediate_results_summary",
                            "query_id": query_id,
                            "summary": summary
                        }
                    }
                    yield f"data: {json.dumps(metadata_chunk, ensure_ascii=False)}\n\n"

            except Exception as e:
                logging.warning(f"获取中间结果摘要失败: {str(e)}")

        # 发送完成标记
        done_chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "graphrag-enhanced",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
        yield f"data: [DONE]\n\n"

        logging.info(f"增强GraphRAG流式响应完成，chat_id: {chat_id}, query: {query[:50]}..., 响应长度: {len(accumulated_content)} 字符")

    # 后台任务：更新数据库
    def background_update():
        final_text = final_content.get("text")
        if final_text:
            logging.info(f'增强GraphRAG Background update: saving final message content (length: {len(final_text)})')
            update_chat_message_background(chat_id, assistant_message_id, final_text)

    return StreamingResponse(
        stream_graphrag_with_results(),
        media_type="text/plain",
        background=BackgroundTask(background_update)
    )


def create_intermediate_results_api_response() -> Dict[str, Any]:
    """
    创建中间结果API响应

    Returns:
        包含所有中间结果摘要的字典
    """
    try:
        # 获取所有中间结果
        all_results = list_all_intermediate_results()

        # 计算统计信息
        total_queries = len(all_results)
        if total_queries > 0:
            avg_time = sum(r.get("total_time", 0) for r in all_results) / total_queries
            total_entities = sum(r.get("entity_mapping", {}).get("selected_entities_count", 0) for r in all_results)
            total_context_tokens = sum(r.get("context_building", {}).get("context_tokens_total", 0) for r in all_results)
        else:
            avg_time = 0
            total_entities = 0
            total_context_tokens = 0

        return {
            "success": True,
            "statistics": {
                "total_queries": total_queries,
                "average_response_time": round(avg_time, 2),
                "total_entities_retrieved": total_entities,
                "total_context_tokens": total_context_tokens
            },
            "results": all_results,
            "details_directory": "./intermediate_results"
        }

    except Exception as e:
        logging.error(f"获取中间结果API响应失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


def get_intermediate_results_detail(query_id: str) -> Dict[str, Any]:
    """
    获取指定查询的详细中间结果

    Args:
        query_id: 查询ID

    Returns:
        详细的中间结果信息
    """
    try:
        # 获取摘要信息
        summary = get_intermediate_results_summary(query_id)
        if not summary:
            return {
                "success": False,
                "error": f"未找到查询ID为 {query_id} 的中间结果"
            }

        # 尝试读取完整结果文件
        full_results_path = summary.get("file_path", "")
        full_results = {}

        if full_results_path and Path(full_results_path).exists():
            try:
                with open(full_results_path, 'r', encoding='utf-8') as f:
                    full_results = json.load(f)
            except Exception as e:
                logging.warning(f"读取完整结果文件失败: {str(e)}")

        return {
            "success": True,
            "summary": summary,
            "full_results": full_results,
            "query_id": query_id
        }

    except Exception as e:
        logging.error(f"获取中间结果详情失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query_id": query_id
        }


def create_intermediate_results_visualization_data() -> Dict[str, Any]:
    """
    创建中间结果可视化数据

    Returns:
        可视化所需的数据结构
    """
    try:
        all_results = list_all_intermediate_results()

        # 时间序列数据
        time_series = []
        for result in all_results:
            timestamp = result.get("timestamp", 0)
            time_series.append({
                "timestamp": timestamp,
                "datetime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)),
                "response_time": result.get("total_time", 0),
                "entities_count": result.get("entity_mapping", {}).get("selected_entities_count", 0),
                "context_tokens": result.get("context_building", {}).get("context_tokens_total", 0)
            })

        # 按时间排序
        time_series.sort(key=lambda x: x["timestamp"])

        # 统计分布
        response_times = [r.get("total_time", 0) for r in all_results if r.get("total_time", 0) > 0]
        entity_counts = [r.get("entity_mapping", {}).get("selected_entities_count", 0) for r in all_results]

        return {
            "success": True,
            "time_series": time_series,
            "statistics": {
                "response_time": {
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "avg": sum(response_times) / len(response_times) if response_times else 0,
                    "median": sorted(response_times)[len(response_times)//2] if response_times else 0
                },
                "entity_counts": {
                    "min": min(entity_counts) if entity_counts else 0,
                    "max": max(entity_counts) if entity_counts else 0,
                    "avg": sum(entity_counts) / len(entity_counts) if entity_counts else 0
                }
            },
            "total_queries": len(all_results)
        }

    except Exception as e:
        logging.error(f"创建可视化数据失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# 使用示例和测试函数
def example_usage():
    """
    使用示例：展示如何在API中集成中间结果收集
    """

    # 示例1: 在FastAPI路由中使用
    """
    @app.post("/chat/enhanced")
    async def enhanced_chat(request: ChatRequest):
        # 获取用户查询
        user_query = request.messages[-1].content if request.messages else ""

        # 使用增强的GraphRAG响应
        return graphrag_stream_response_with_intermediate_results(
            chat_id="demo_chat",
            query=user_query,
            user_message_id="user_123",
            assistant_message_id="assistant_123",
            enable_intermediate_collection=True
        )

    @app.get("/intermediate-results")
    async def get_intermediate_results():
        return create_intermediate_results_api_response()

    @app.get("/intermediate-results/{query_id}")
    async def get_intermediate_result_detail(query_id: str):
        return get_intermediate_results_detail(query_id)

    @app.get("/intermediate-results/visualization")
    async def get_visualization_data():
        return create_intermediate_results_visualization_data()
    """

    print("示例代码已在注释中提供，请参考上述注释在FastAPI应用中集成")


if __name__ == "__main__":
    # 运行示例
    example_usage()

    # 演示数据结构
    print("\n=== 中间结果数据结构示例 ===")

    # 模拟创建一些测试数据
    sample_results = create_intermediate_results_api_response()
    print("API响应结构:")
    print(json.dumps(sample_results, ensure_ascii=False, indent=2))