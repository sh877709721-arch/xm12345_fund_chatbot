"""
增强版 GraphRAG 查询模块，支持中间结果提取

基于原有 query_graphrag.py 进行扩展，添加中间结果收集功能
"""

import asyncio
import json
import time
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, Any, List

import pandas as pd
import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

from app.core.graph.intermediate_results import (
    IntermediateResultsCollector,
    EnhancedLocalSearchMixedContext
)


# 项目配置
PROJECT_DIRECTORY = "./app/core/graph/chatbot_zh"

# 加载配置和数据（与原文件相同）
graphrag_config = load_config(Path(PROJECT_DIRECTORY))

# 加载数据
entities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/entities.parquet")
communities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/communities.parquet")
community_reports = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/community_reports.parquet")
text_units = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/text_units.parquet")
relationships = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/relationships.parquet")
covariates = None

# 全局结果收集器
_global_collector: Optional[IntermediateResultsCollector] = None


def set_global_collector(collector: IntermediateResultsCollector):
    """设置全局结果收集器"""
    global _global_collector
    _global_collector = collector


def get_global_collector() -> Optional[IntermediateResultsCollector]:
    """获取全局结果收集器"""
    return _global_collector


async def rag_chatbot_local_search_stream_with_results(
    query: str,
    query_id: Optional[str] = None,
    collect_results: bool = True
) -> AsyncGenerator[str, None]:
    """
    增强版本地搜索流式查询，支持中间结果收集

    Args:
        query: 查询问题
        query_id: 查询ID，用于标识唯一查询
        collect_results: 是否收集中间结果

    Yields:
        str: 流式响应内容
    """
    if not query_id:
        query_id = f"query_{int(time.time() * 1000)}"

    # 创建结果收集器
    collector = None
    if collect_results:
        collector = IntermediateResultsCollector()
        collector.start_collection(query_id, query)
        set_global_collector(collector)

    try:
        start_time = time.time()

        # 执行原始的GraphRAG本地搜索
        response_parts = []

        # 这里我们通过hook方式收集中间结果
        async for chunk in _enhanced_local_search_streaming_with_hooks(
            query=query,
            collector=collector
        ):
            response_parts.append(chunk)
            yield chunk

        total_time = time.time() - start_time

        # 保存最终结果
        if collector:
            final_response = ''.join(response_parts)
            collector.collect_final_prompt(final_response)
            collector.finish_collection()

            # 异步保存结果文件（不阻塞响应）
            asyncio.create_task(_save_results_async(collector))

    except Exception as e:
        print(f"查询过程中发生错误: {str(e)}")
        # 即使出错也尝试保存已收集的结果
        if collector:
            try:
                collector.finish_collection()
                asyncio.create_task(_save_results_async(collector))
            except:
                pass
        raise


async def _enhanced_local_search_streaming_with_hooks(
    query: str,
    collector: Optional[IntermediateResultsCollector] = None
) -> AsyncGenerator[str, None]:
    """
    带hooks的本地搜索流式执行
    """
    # 由于无法直接修改GraphRAG内部实现，我们使用monkey patch的方式
    # 这里简化处理，实际使用时需要更精细的hook机制

    vector_search_start = time.time()

    # 模拟向量检索阶段（实际应该hook到GraphRAG内部）
    # 在真实实现中，这里应该是GraphRAG的实际调用
    response_chunks = []

    try:
        # 调用原始的GraphRAG本地搜索
        async for chunk in api.local_search_streaming(
            config=graphrag_config,
            entities=entities,
            communities=communities,
            community_reports=community_reports,
            text_units=text_units,
            relationships=relationships,
            covariates=covariates,
            community_level=2,
            response_type="Multiple Paragraphs",
            query=query,
            verbose=True
        ):
            response_chunks.append(chunk)

            # 如果有收集器，实时收集部分信息
            if collector and chunk:
                # 这里可以解析chunk内容，提取有用的中间信息
                pass

            yield chunk

    except Exception as e:
        print(f"GraphRAG搜索错误: {str(e)}")
        yield f"搜索过程中发生错误: {str(e)}"


async def _save_results_async(collector: IntermediateResultsCollector):
    """异步保存结果"""
    try:
        filepath = collector.save_results()
        print(f"中间结果已保存到: {filepath}")

        # 可选：保存摘要到单独文件
        summary = collector.get_summary()
        summary_filepath = filepath.replace('.json', '_summary.json')
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"保存中间结果失败: {str(e)}")


def get_intermediate_results_summary(query_id: str) -> Optional[Dict[str, Any]]:
    """
    获取指定查询的中间结果摘要

    Args:
        query_id: 查询ID

    Returns:
        中间结果摘要，如果不存在则返回None
    """
    results_dir = Path("./intermediate_results")

    # 查找匹配的文件
    for file_path in results_dir.glob(f"intermediate_results_{query_id}_*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                results_data = json.load(f)

            # 生成摘要
            summary = {
                "query_id": results_data.get("query_id"),
                "timestamp": results_data.get("timestamp"),
                "total_time": results_data.get("total_time"),
                "original_query": results_data.get("original_query"),
                "file_path": str(file_path)
            }

            # 添加向量搜索摘要
            if "vector_search" in results_data and results_data["vector_search"]:
                vs = results_data["vector_search"]
                summary["vector_search"] = {
                    "matched_entities_count": len(vs.get("matched_entities", [])),
                    "search_time": vs.get("search_time", 0),
                    "avg_similarity_score": sum(vs.get("similarity_scores", [])) / len(vs.get("similarity_scores", [1])) if vs.get("similarity_scores") else 0
                }

            # 添加实体映射摘要
            if "entity_mapping" in results_data and results_data["entity_mapping"]:
                em = results_data["entity_mapping"]
                summary["entity_mapping"] = {
                    "selected_entities_count": em.get("entity_count", 0),
                    "excluded_entities_count": len(em.get("excluded_entities", [])),
                    "included_entities_count": len(em.get("included_entities", []))
                }

            # 添加上下文构建摘要
            if "context_building" in results_data and results_data["context_building"]:
                cb = results_data["context_building"]
                summary["context_building"] = {
                    "final_context_length": len(cb.get("final_context", "")),
                    "context_tokens_total": sum(cb.get("context_tokens", {}).values()),
                    "context_sections": list(cb.get("context_tokens", {}).keys())
                }

            return summary

        except Exception as e:
            print(f"读取结果文件失败 {file_path}: {str(e)}")
            continue

    return None


def list_all_intermediate_results() -> List[Dict[str, Any]]:
    """
    列出所有可用的中间结果

    Returns:
        所有中间结果的摘要列表
    """
    results_dir = Path("./intermediate_results")
    if not results_dir.exists():
        return []

    summaries = []
    for file_path in results_dir.glob("intermediate_results_*_summary.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                summary["summary_file_path"] = str(file_path)
                summary["full_results_file_path"] = str(file_path).replace("_summary.json", ".json")
                summaries.append(summary)
        except Exception as e:
            print(f"读取摘要文件失败 {file_path}: {str(e)}")

    # 按时间戳排序
    summaries.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return summaries


# 向后兼容的函数
async def rag_chatbot_global_search(query: str) -> str:
    """保持原有API兼容性"""
    response, context = await api.global_search(
        config=graphrag_config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        community_level=2,
        dynamic_community_selection=False,
        response_type="Multiple Paragraphs",
        query=query,
    )
    return response


async def rag_chatbot_stream(query: str):
    """保持原有API兼容性"""
    async for chunk in api.global_search_streaming(
        config=graphrag_config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        community_level=2,
        dynamic_community_selection=False,
        response_type="Multiple Paragraphs",
        query=query,
        verbose=True
    ):
        yield chunk


async def rag_chatbot_local_search(query: str) -> str:
    """保持原有API兼容性"""
    response, context = await api.local_search(
        config=graphrag_config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        text_units=text_units,
        relationships=relationships,
        covariates=covariates,
        community_level=2,
        response_type="Multiple Paragraphs",
        query=query,
    )
    return response


async def rag_chatbot_local_search_stream(query: str):
    """保持原有API兼容性"""
    async for chunk in api.local_search_streaming(
        config=graphrag_config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        text_units=text_units,
        relationships=relationships,
        covariates=covariates,
        community_level=2,
        response_type="Multiple Paragraphs",
        query=query,
        verbose=True
    ):
        yield chunk


if __name__ == "__main__":
    # 测试代码
    async def test_enhanced_search():
        test_query = "什么是机器学习？"
        query_id = "test_001"

        print(f"开始测试增强搜索，查询: {test_query}")

        # 执行增强搜索
        response_parts = []
        async for chunk in rag_chatbot_local_search_stream_with_results(
            query=test_query,
            query_id=query_id,
            collect_results=True
        ):
            response_parts.append(chunk)
            print(f"收到响应块: {chunk[:50]}...")

        final_response = ''.join(response_parts)
        print(f"\n最终响应: {final_response}")

        # 获取中间结果摘要
        summary = get_intermediate_results_summary(query_id)
        print(f"\n中间结果摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")

        # 列出所有结果
        all_results = list_all_intermediate_results()
        print(f"\n所有中间结果数量: {len(all_results)}")

    # 运行测试
    # asyncio.run(test_enhanced_search())