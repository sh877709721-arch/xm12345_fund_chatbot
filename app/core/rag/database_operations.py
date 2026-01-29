"""
数据库操作模块
负责数据库查询执行、统计信息获取等数据库相关操作
"""

from typing import List, Dict, Tuple
from sqlalchemy import text
from app.config.database import SessionLocal,global_schema


class DatabaseOperations:
    """数据库操作类"""

    @staticmethod
    def execute_search(sql, params: Dict = None) -> List[Dict]:
        """
        执行搜索查询并返回结果

        Args:
            sql: SQL查询语句
            params: 查询参数，默认为None

        Returns:
            查询结果列表
        """
        with SessionLocal() as session:
            if params:
                result = session.execute(sql, params)
            else:
                result = session.execute(sql)
            rows = result.fetchall()
            if not rows:
                return []
            # 获取列名
            columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    def get_collection_stats(table_name: str) -> Tuple[float, int]:
        """
        获取文档集合的统计信息

        Args:
            table_name: 表名

        Returns:
            (avg_doc_length, total_docs): 平均文档长度和总文档数
        """
        sql = text(f"""
            SELECT
                AVG(LENGTH(content)) as avg_doc_length,
                COUNT(*) as total_docs
            FROM {table_name}
            WHERE content IS NOT NULL
        """)

        with SessionLocal() as session:
            result = session.execute(sql)
            row = result.fetchone()
            if row is None or row[0] is None:
                return 0.0, 0
            return float(row[0]), int(row[1])
    
    @staticmethod
    def get_index_knowledge_collection_stats() -> Tuple[float, int]:
        """
        获取文档集合的统计信息

        Args:
            table_name: 表名

        Returns:
            (avg_doc_length, total_docs): 平均文档长度和总文档数
        """
        sql = text(f"""
            SELECT
                AVG(LENGTH(content)) as avg_doc_length,
                COUNT(*) as total_docs
            FROM {global_schema}.indexed_knowledge 
            WHERE knowledge_type = 'document'
                AND status = 'P'
        """)

        with SessionLocal() as session:
            result = session.execute(sql)
            row = result.fetchone()
            if row is None or row[0] is None:
                return 0.0, 0
            return float(row[0]), int(row[1])

    @staticmethod
    def execute_rerank_query(sql: text, params: Dict) -> List[Dict]:
        """
        执行带有rerank的查询

        Args:
            sql: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        with SessionLocal() as session:
            result = session.execute(sql, params)
            rows = result.fetchall()
        return [{
            "id": row[0], 
            "question": row[1], 
            "answer": row[2],
            "reference": row[3],
            "hybrid_score": row[3]
            } 
            for row in rows
        ]

    @staticmethod
    def format_embedding_vector(embedding: List[float]) -> str:
        """
        将嵌入向量格式化为PostgreSQL vector格式

        Args:
            embedding: 嵌入向量列表

        Returns:
            PostgreSQL vector格式的字符串
        """
        return f'[{",".join(map(str, embedding))}]'