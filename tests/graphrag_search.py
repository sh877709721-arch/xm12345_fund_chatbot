import logging
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



from app.core.graph.enhanced_query_graphrag import get_intermediate_results_summary

# 获取特定查询的中间结果摘要
summary = get_intermediate_results_summary("医疗保险")
print(f"summary: {summary}")