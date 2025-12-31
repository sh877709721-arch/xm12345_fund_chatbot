from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json5
import pytz

from pathlib import Path
from pprint import pprint

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

# Initialize FastMCP server
mcp = FastMCP("knowledge_graph")

@mcp.tool()
async def graph_rag(query: str) -> str:
    """
    :param query: 问题
    :return: query 问题对应的答案
    """
    PROJECT_DIRECTORY = "./MLRAG"
    graphrag_config = load_config(Path(PROJECT_DIRECTORY))
    
    # 加载实体
    entities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/entities.parquet")
    # 加载社区
    communities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/communities.parquet")
    # 加载社区报告
    community_reports = pd.read_parquet(
        f"{PROJECT_DIRECTORY}/output/community_reports.parquet"
    )
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
    
    return response
def main():
    # Initialize and run the server
    mcp.run(transport='stdio')    


if __name__ == '__main__':
    main()