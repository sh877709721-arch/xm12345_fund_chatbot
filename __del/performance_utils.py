"""
性能优化工具模块
提供数据库索引创建建议、缓存优化策略等性能优化相关工具
"""


class PerformanceOptimizer:
    """性能优化工具类"""

    @staticmethod
    def create_indexes():
        """
        创建性能优化索引（在数据库中执行）

        注意：这些 SQL 语句需要在数据库中手动执行或通过数据库迁移工具执行
        """
        index_sqls = [
            # 为 BM25 搜索优化
            """
            -- 创建文档长度索引（用于 BM25 长度归一化）
            CREATE INDEX IF NOT EXISTS idx_doc_knowledge_content_length
            ON chatbot.doc_knowledge(LENGTH(content));
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_qa_knowledge_content_length
            ON chatbot.qa_knowledge(LENGTH(content));
            """,

            # 为向量搜索优化
            """
            -- 为向量相似度搜索创建 IVFFLAT 索引（如果支持）
            -- CREATE INDEX IF NOT EXISTS idx_doc_knowledge_q_embedding_ivf
            -- ON chatbot.doc_knowledge USING ivfflat (q_embedding vector_cosine_ops)
            -- WITH (lists = 100);
            """,

            # 为混合查询优化
            """
            -- 复合索引优化
            CREATE INDEX IF NOT EXISTS idx_doc_knowledge_fts_length
            ON chatbot.doc_knowledge USING gin(fts)
            INCLUDE (id, title, content);
            """,

            """
            CREATE INDEX IF NOT EXISTS idx_qa_knowledge_fts_length
            ON chatbot.qa_knowledge USING gin(fts)
            INCLUDE (id, question, content);
            """
        ]

        print("建议在数据库中执行以下索引优化语句:")
        for sql in index_sqls:
            print(sql.strip())
            print()

    @staticmethod
    def cache_optimization():
        """
        缓存优化建议
        """
        print("缓存优化建议:")
        print("1. 向量嵌入缓存:")
        print("   - 对常见查询进行向量化结果缓存")
        print("   - 使用 Redis 或内存缓存存储嵌入向量")
        print()
        print("2. 搜索结果缓存:")
        print("   - 缓存热门查询的搜索结果")
        print("   - 设置合适的 TTL（如 5-15 分钟）")
        print()
        print("3. 统计信息缓存:")
        print("   - 缓存文档集合统计信息（平均文档长度、文档总数）")
        print("   - 只在数据更新时重新计算")
        print()
        print("4. 预计算优化:")
        print("   - 预计算热门查询词的 BM25 评分")
        print("   - 建立查询-文档的倒排索引缓存")

    @staticmethod
    def get_search_tips():
        """
        搜索性能优化建议
        """
        print("搜索性能优化建议:")
        print("1. 查询优化:")
        print("   - 使用适当的相似度阈值减少候选集")
        print("   - 合理设置 LIMIT 限制结果数量")
        print("   - 优先使用索引字段进行过滤")
        print()
        print("2. 并行处理:")
        print("   - 并行执行 BM25 和向量搜索")
        print("   - 使用连接池优化数据库连接")
        print("   - 合理设置线程池大小")
        print()
        print("3. 内存优化:")
        print("   - 及时释放不需要的向量数据")
        print("   - 使用生成器处理大量结果")
        print("   - 分批处理大型数据集")