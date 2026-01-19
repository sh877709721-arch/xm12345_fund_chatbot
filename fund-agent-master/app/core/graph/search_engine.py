
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

from graphrag.query.indexer_adapters import (
read_indexer_communities,
read_indexer_covariates,
read_indexer_entities,
    read_indexer_relationships,
    read_indexer_report_embeddings,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.utils.api import (
    get_embedding_store,
    load_search_prompt,
    truncate,
    update_context_data,
)
from graphrag.config.embeddings import (
    community_full_content_embedding,
    entity_description_embedding,
    text_unit_text_embedding,
)
from graphrag.query.factory import (
    get_basic_search_engine,
    get_drift_search_engine,
    get_global_search_engine,
    get_local_search_engine,
)
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.language_model.manager import ModelManager
from graphrag.utils.cli import redact


config = graphrag_config
vector_store_args = {}
for index, store in config.vector_store.items():
    vector_store_args[index] = store.model_dump()
msg = f"Vector Store Args: {redact(vector_store_args)}"
print(msg)

description_embedding_store = get_embedding_store(
    config_args=vector_store_args,
    embedding_name=entity_description_embedding,
)

# 为基础搜索和 DRIFT 搜索初始化文本单元向量存储
text_unit_embedding_store = get_embedding_store(
    config_args=vector_store_args,
    embedding_name=text_unit_text_embedding,
)

# 为全局搜索初始化社区报告向量存储
community_embedding_store = get_embedding_store(
    config_args=vector_store_args,
    embedding_name=community_full_content_embedding,
)

entities_ = read_indexer_entities(entities, communities, community_level=2)
covariates_ = read_indexer_covariates(covariates) if covariates is not None else []
prompt = load_search_prompt(config.root_dir, config.local_search.prompt)


def get_local_search_context(query):
    search_engine = get_local_search_engine(
        config=config,
        reports=read_indexer_reports(community_reports, communities, community_level=2),
        text_units=read_indexer_text_units(text_units),
        entities=entities_,
        relationships=read_indexer_relationships(relationships),
        covariates={"claims": covariates_},
        description_embedding_store=description_embedding_store,
        response_type="Multiple Paragraphs",
        system_prompt=prompt,
        callbacks=None,
    )
    

    search_engine.stream_search(query=query)
    context_result = search_engine.context_builder.build_context(
            query=query,
            conversation_history=None,
            **search_engine.context_builder_params,
    )
    
    return context_result,search_engine.system_prompt


def get_basic_search_context(query):
    """基础搜索上下文生成函数

    用于简单的语义搜索和文本匹配，适合不需要复杂推理的查询。

    Args:
        query: 搜索查询字符串

    Returns:
        (context_result, system_prompt): 上下文结果和系统提示词
    """
    basic_prompt = load_search_prompt(config.root_dir, config.basic_search.prompt)

    search_engine = get_basic_search_engine(
        text_units=read_indexer_text_units(text_units),
        text_unit_embeddings=text_unit_embedding_store,
        config=config,
        system_prompt=basic_prompt,
        response_type="Multiple Paragraphs",
        callbacks=None,
    )

    search_engine.stream_search(query=query)
    context_result = search_engine.context_builder.build_context(
        query=query,
        conversation_history=None,
        **search_engine.context_builder_params,
    )

    return context_result, search_engine.system_prompt


def get_drift_search_context(query):
    """DRIFT 搜索上下文生成函数

    分布式检索方法，结合本地和全局搜索特点，适合复杂查询。

    Args:
        query: 搜索查询字符串

    Returns:
        (context_result, local_prompt): 上下文结果和本地系统提示词
    """
    local_prompt = load_search_prompt(config.root_dir, config.drift_search.prompt)
    reduce_prompt = load_search_prompt(config.root_dir, config.drift_search.reduce_prompt)

    search_engine = get_drift_search_engine(
        config=config,
        reports=read_indexer_reports(community_reports, communities, community_level=2),
        text_units=read_indexer_text_units(text_units),
        entities=entities_,
        relationships=read_indexer_relationships(relationships),
        description_embedding_store=description_embedding_store,
        response_type="Multiple Paragraphs",
        local_system_prompt=local_prompt,
        reduce_system_prompt=reduce_prompt,
        callbacks=None,
    )

    search_engine.stream_search(query=query)
    context_result = search_engine.context_builder.build_context(
        query=query,
        conversation_history=None,
        **search_engine.context_builder_params,
    )

    return context_result, search_engine.context_builder.local_system_prompt


def get_global_search_context(query):
    """全局搜索上下文生成函数

    在整个知识图谱中搜索，适合需要跨社区理解的广泛查询。

    Args:
        query: 搜索查询字符串

    Returns:
        (context_result, map_prompt): 上下文结果和 map 系统提示词
    """
    map_prompt = load_search_prompt(config.root_dir, config.global_search.map_prompt)
    reduce_prompt = load_search_prompt(config.root_dir, config.global_search.reduce_prompt)

    search_engine = get_global_search_engine(
        config=config,
        reports=read_indexer_reports(community_reports, communities, community_level=2),
        entities=entities_,
        communities=read_indexer_communities(communities, community_reports),
        response_type="Multiple Paragraphs",
        map_system_prompt=map_prompt,
        reduce_system_prompt=reduce_prompt,
        dynamic_community_selection=False,
        callbacks=None,
    )

    search_engine.stream_search(query=query)
    context_result = search_engine.context_builder.build_context(
        query=query,
        conversation_history=None,
        **search_engine.context_builder_params,
    )

    return context_result, search_engine.map_system_prompt


async def get_global_search_context_v2(query):
    """全局搜索上下文生成函数 V2

    严格按照官方 notebook 示例实现，直接使用 GlobalSearch 类而非工厂方法。
    在整个知识图谱中搜索，适合需要跨社区理解的广泛查询。

    Args:
        query: 搜索查询字符串

    Returns:
        (context_result, context_data): 上下文结果和上下文数据
    """
    # 加载数据
    COMMUNITY_LEVEL = 2

    # 准备数据
    communities_v2 = read_indexer_communities(communities, community_reports)
    reports_v2 = read_indexer_reports(community_reports, communities, COMMUNITY_LEVEL)
    entities_v2 = read_indexer_entities(entities, communities, COMMUNITY_LEVEL)

    # 获取模型和 tokenizer
    model_settings = config.get_language_model_config(config.global_search.chat_model_id)
    model = ModelManager().get_or_create_chat_model(
        name="global_search",
        model_type=model_settings.type,
        config=model_settings,
    )
    tokenizer = get_tokenizer(model_config=model_settings)

    # 构建 context builder
    context_builder = GlobalCommunityContext(
        community_reports=reports_v2,
        communities=communities_v2,
        entities=entities_v2,
        tokenizer=tokenizer,
    )

    # 配置参数
    context_builder_params = {
        "use_community_summary": False,  # False means using full community reports
        "shuffle_data": True,
        "include_community_rank": True,
        "min_community_rank": 0,
        "community_rank_name": "rank",
        "include_community_weight": True,
        "community_weight_name": "occurrence weight",
        "normalize_community_weight": True,
        "max_context_tokens": config.global_search.max_context_tokens,
        "context_name": "Reports",
    }

    map_llm_params = {
        "max_tokens": config.global_search.map_max_length,
        "temperature": 0.0,
    }

    reduce_llm_params = {
        "max_tokens": config.global_search.reduce_max_length,
        "temperature": 0.0,
    }

    # 创建搜索引擎
    search_engine = GlobalSearch(
        model=model,
        context_builder=context_builder,
        tokenizer=tokenizer,
        max_data_tokens=config.global_search.data_max_tokens,
        map_llm_params=map_llm_params,
        reduce_llm_params=reduce_llm_params,
        allow_general_knowledge=False,
        json_mode=True,
        context_builder_params=context_builder_params,
        concurrent_coroutines=model_settings.concurrent_requests,
        response_type="Multiple Paragraphs",
    )

    # 执行搜索并获取结果
    result = await search_engine.search(query=query)

    return result, result.context_data

