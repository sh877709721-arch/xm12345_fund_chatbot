from typing import List, Optional
from sqlalchemy import update, or_
from sqlalchemy.orm import Session

from app.model.knowledge_index import IndexedKnowledge
from app.schema.base import BaseResponse
from app.config.settings import settings
from app.config.llm_client import embedding_client
from typing import Literal
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sql_text
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config.database import global_schema
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
BATCH_SIZE = 2
MODEL_NAME = "bge-m3"
EMBEDDING_DIM = 1024

class KnowledgeIndexService:
    def __init__(self, db: Session):
        self.db = db


    def generate_embeddings(self,texts: List[str]) -> List[List[float]]:
        """调用 embedding 服务，返回 float 列表的列表"""
        if not texts:
            return []
        try:
            response = embedding_client.embeddings.create(
                input=texts,
                model=MODEL_NAME
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            embeddings = [emb.embedding for emb in sorted_data]
            # 校验维度
            for emb in embeddings:
                if len(emb) != EMBEDDING_DIM:
                    raise ValueError(f"Embedding 维度错误：期望 {EMBEDDING_DIM}，实际 {len(emb)}")
            return embeddings
        except Exception as e:
            logger.error(f"❌ Embedding 生成失败: {e}")
            raise

    def update_knowledge_pending_by_id(self, knowledge_id):
        """修改索引后的知识，置为待审核 P"""
        try:
            # 使用原生SQL将指定knowledge_id的记录状态置为'P'
            update_query = f"""
                UPDATE {global_schema}.indexed_knowledge
                SET status = 'P', updated_time = NOW()
                WHERE knowledge_id = {knowledge_id}
            """

            result = self.db.execute(sql_text(update_query))

            if result == 0:
                raise ValueError("Knowledge not found")
            

            self.db.commit()
            return {"message": f"Knowledge {knowledge_id} updated to pending status successfully"}
        except Exception as e:
            self.db.rollback()
            raise e
        
    
    def add_knowledge_active_by_id(self, knowledge_id):
        """根据 knowledge_id 重新索引知识并置为激活状态 A"""
        try:
            # 1. 查询知识信息
            query = f"""
                SELECT a.id as knowledge_id, a.knowledge_type, a.name as title, b.content, b.reference
                FROM {global_schema}.knowledge a
                INNER JOIN {global_schema}.knowledge_detail b ON a.id = b.knowledge_id
                WHERE a.status <> 'deleted' AND b.status <> 'deleted' AND a.id = {knowledge_id}
                ORDER BY a.id ASC
            """

            result = self.db.execute(sql_text(query))
            knowledge_data = result.fetchall()

            if not knowledge_data:
                raise ValueError(f"Knowledge with id {knowledge_id} not found")

            knowledge_row = knowledge_data[0]
            knowledge_type = knowledge_row.knowledge_type
            title = knowledge_row.title or ""
            content = knowledge_row.content or ""
            reference = knowledge_row.reference or ""

            # 初始化 chunks 变量
            chunks = []

            # 2. 先将知识表和知识详情表状态从 pending 转为 active
            update_knowledge_query = f"""
                UPDATE {global_schema}.knowledge
                SET status = 'active'
                WHERE id = {knowledge_id} AND status = 'pending'
            """
            self.db.execute(sql_text(update_knowledge_query))

            update_detail_query = f"""
                UPDATE {global_schema}.knowledge_detail
                SET status = 'active'
                WHERE knowledge_id = {knowledge_id} AND status = 'pending'
            """
            self.db.execute(sql_text(update_detail_query))

            logger.info(f"✅ 知识 {knowledge_id} 状态已从 pending 转为 active")

            # 3. 将现有索引状态置为待审核 P（使用原生SQL）
            update_pending_query = f"""
                UPDATE {global_schema}.indexed_knowledge
                SET status = 'P', updated_time = NOW()
                WHERE knowledge_id = {knowledge_id}
            """
            self.db.execute(sql_text(update_pending_query))

            # 4. 根据知识类型处理
            if knowledge_type == 'qa':
                # QA类型：直接生成embedding
                texts = [title, content]
                embeddings = self.generate_embeddings(texts)

                if len(embeddings) >= 2:
                    # 将embedding转换为vector字符串格式
                    q_embedding_str = f"[{','.join(map(str, embeddings[0]))}]"
                    a_embedding_str = f"[{','.join(map(str, embeddings[1]))}]"

                    # 插入新的索引记录（使用原生SQL支持vector类型）
                    insert_query = f"""
                        INSERT INTO {global_schema}.indexed_knowledge
                        (knowledge_id, knowledge_type, title, content, reference, q_embedding, a_embedding, status, created_time, updated_time)
                        VALUES
                        ({knowledge_id}, '{knowledge_type}', $title${title}$title$, $content${content}$content$, $reference${reference}$reference$,
                         '{q_embedding_str}'::vector, '{a_embedding_str}'::vector, 'A', NOW(), NOW())
                    """
                    self.db.execute(sql_text(insert_query))
                    logger.info(f"✅ QA 知识 {knowledge_id} 索引创建成功")

            elif knowledge_type == 'document':
                # 文档类型：需要分块处理
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1200,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["######"]
                )

                # 分块
                chunks = text_splitter.split_text(content)

                # 为每个块生成embedding并插入
                for i, chunk in enumerate(chunks):
                    chunk_title = f"{title}_chunk_{i+1}" if len(chunks) > 1 else title
                    texts = [chunk_title, chunk]
                    embeddings = self.generate_embeddings(texts)

                    if len(embeddings) >= 2:
                        # 将embedding转换为vector字符串格式
                        q_embedding_str = f"[{','.join(map(str, embeddings[0]))}]"
                        a_embedding_str = f"[{','.join(map(str, embeddings[1]))}]"

                        # 插入新的索引记录
                        insert_query = f"""
                            INSERT INTO {global_schema}.indexed_knowledge
                            (knowledge_id, knowledge_type, title, content, reference, q_embedding, a_embedding, status, created_time, updated_time)
                            VALUES
                            ({knowledge_id}, '{knowledge_type}', $title${chunk_title}$title$, $content${chunk}$content$, $reference${reference}$reference$,
                             '{q_embedding_str}'::vector, '{a_embedding_str}'::vector, 'A', NOW(), NOW())
                        """
                        self.db.execute(sql_text(insert_query))

                logger.info(f"✅ 文档知识 {knowledge_id} 分为 {len(chunks)} 块，索引创建成功")

            # 4. 更新FTS字段（如果需要）
            fts_update_query = f"""
                UPDATE {global_schema}.indexed_knowledge
                SET fts =
                    setweight(to_tsvector('zhparsercfg', coalesce(title, '')), 'A') ||
                    setweight(to_tsvector('zhparsercfg', coalesce(content, '')), 'B')
                WHERE knowledge_id = {knowledge_id} AND status = 'A'
            """
            self.db.execute(sql_text(fts_update_query))

            self.db.commit()

            return {
                "message": f"Knowledge {knowledge_id} reindexed and activated successfully",
                "knowledge_type": knowledge_type,
                "chunks_count": 1 if knowledge_type == 'qa' else len(chunks) if knowledge_type == 'document' else 0
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 知识索引失败: {e}")
            raise e