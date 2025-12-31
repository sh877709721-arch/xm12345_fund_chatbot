from pathlib import Path
from pprint import pprint

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

PROJECT_DIRECTORY = "./app/core/graph/chatbot_zh"

graphrag_config = load_config(Path(PROJECT_DIRECTORY))

# 加载实体
entities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/entities.parquet")
# 加载社区
communities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/communities.parquet")
# 加载社区报告
community_reports = pd.read_parquet(
    f"{PROJECT_DIRECTORY}/output/community_reports.parquet"
)
# 加载文本单元
text_units = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/text_units.parquet")
# 加载关系
relationships = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/relationships.parquet")
# covariates 可能不存在，设置为 None
covariates = None


async def rag_chatbot_global_search(query: str) -> str:
    """
    :param query: 问题
    :return: query问题对应的答案
    """
    # 进行全局搜索
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
    
    pprint(context)
    return response

async def rag_chatbot_stream(query: str):
    """
    使用流式方式执行 GraphRAG 全局搜索

    :param query: 问题
    :return: 异步生成器，逐块返回搜索结果
    """
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
        # 逐块返回流式响应
        yield chunk


async def rag_chatbot_local_search(query: str) -> str:
    """
    执行 GraphRAG 本地搜索

    :param query: 问题
    :return: query问题对应的答案
    """
    # 进行本地搜索
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

    pprint(context)
    return response


async def rag_chatbot_local_search_stream(query: str):
    """
    使用流式方式执行 GraphRAG 本地搜索

    :param query: 问题
    :return: 异步生成器，逐块返回搜索结果
    """
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
        # 逐块返回流式响应
        yield chunk

