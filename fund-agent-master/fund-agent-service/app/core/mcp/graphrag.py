from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json5
import pytz

from pathlib import Path
from pprint import pprint

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from app.core.graph.search_engine import get_local_search_context

# Initialize FastMCP server
mcp = FastMCP("knowledge_graph")

@mcp.tool()
async def graph_rag(query: str):
    """
    :param query: 问题
    :return: query 问题对应的答案
    """
    graph_context,system_prompt=get_local_search_context(query)
    
    return graph_context
def main():
    # Initialize and run the server
    mcp.run(transport='stdio')    


if __name__ == '__main__':
    main()