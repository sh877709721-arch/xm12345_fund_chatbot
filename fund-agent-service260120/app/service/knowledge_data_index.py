from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import text as sql_text
import pandas as pd
import logging
from io import BytesIO
from app.config.database import global_schema
from app.model.knowledge import KnowledgeData, KnowledgeStatusEnum
from app.core.embeddings_utils import get_text_embeddings_default

logger = logging.getLogger(__name__)


class KnowledgeDataIndexService:
    """Excel 数据索引服务"""

    def __init__(self, db: Session):
        self.db = db

    def parse_excel_to_jsonb(
        self,
        file_content: bytes,
        sheet_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        解析 Excel 文件为 JSON 格式

        Args:
            file_content: Excel 文件内容（字节）
            sheet_name: 工作表名称（默认第一个）

        Returns:
            对象数组: [{列1: 值1, 列2: 值2}, ...]
        """
        try:
            # 读取 Excel
            df = pd.read_excel(
                BytesIO(file_content),
                sheet_name=sheet_name or 0
            )

            # 处理 NaN 值
            df = df.fillna("")

            # 转换为对象数组
            data = df.to_dict('records')

            logger.info(f"✅ Excel 解析成功: {len(data)} 行, {len(df.columns)} 列")

            return data

        except Exception as e:
            logger.error(f"❌ Excel 解析失败: {e}")
            raise ValueError(f"Excel 文件格式错误: {e}")

    def save_knowledge_data_row(
        self,
        knowledge_id: int,
        row_data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> KnowledgeData:
        """
        保存单行知识数据到 knowledge_data 表

        Args:
            knowledge_id: 知识ID
            row_data: 单行数据（对象格式）
            created_by: 创建人ID

        Returns:
            KnowledgeData 实例
        """
        try:
            # 创建新记录（每行一条记录）
            knowledge_data = KnowledgeData(
                knowledge_id=knowledge_id,
                content=row_data,  # 存储单行数据
                status=KnowledgeStatusEnum.active,
                created_by=created_by
            )

            self.db.add(knowledge_data)
            self.db.flush()  # ✅ 使用 flush 获取 ID，但不立即提交整个事务

            return knowledge_data

        except Exception as e:
            self.db.rollback()  # ✅ 发生异常时回滚
            logger.error(f"❌ 数据行保存失败: {e}")
            raise

    def create_fts_index_for_row(
        self,
        knowledge_data: KnowledgeData
    ) -> bool:
        """
        为单行数据创建全文搜索索引和向量索引

        Args:
            knowledge_data: KnowledgeData 实例

        Returns:
            是否成功
        """
        try:
            # 提取该行数据的所有文本，保留键值对结构（包含表头信息）
            row_text = " ".join(
                f"{k}:{v}"
                for k, v in knowledge_data.content.items()
                if v is not None and str(v).strip()
            )

            # ✅ 空文本检查
            if not row_text:
                logger.warning(f"⚠️ 行数据 {knowledge_data.id} 没有可索引的文本内容")
                return True

            # 1. 获取文本向量
            embedding = get_text_embeddings_default(row_text)
            vector_str = None

            if not embedding:
                logger.warning(f"⚠️ 行数据 {knowledge_data.id} 向量化失败")
            else:
                # 将向量转换为 PostgreSQL vector 格式 '[val1,val2,...]'
                vector_str = f'[{",".join(map(str, embedding))}]'

            # 2. 更新 FTS 索引和向量索引（使用 UPDATE 语句）
            if embedding and vector_str:
                update_query = sql_text(f"""
                    UPDATE {global_schema}.knowledge_data
                    SET fts_content = to_tsvector('zhparsercfg', :text_content),
                        fts_vector = :vector_str
                    WHERE id = :knowledge_data_id
                """)
                self.db.execute(update_query, {
                    "knowledge_data_id": knowledge_data.id,
                    "text_content": row_text,
                    "vector_str": vector_str
                })
            else:
                # 如果向量化失败，只更新 FTS 索引
                update_query = sql_text(f"""
                    UPDATE {global_schema}.knowledge_data
                    SET fts_content = to_tsvector('zhparsercfg', :text_content)
                    WHERE id = :knowledge_data_id
                """)
                self.db.execute(update_query, {
                    "knowledge_data_id": knowledge_data.id,
                    "text_content": row_text
                })

            return True

        except Exception as e:
            logger.error(f"❌ 索引创建失败 (ID: {knowledge_data.id}): {e}")
            raise

    def process_excel_upload(
        self,
        knowledge_id: int,
        file_content: bytes,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        完整的 Excel 上传处理流程（每行一条记录）

        Args:
            knowledge_id: 知识ID
            file_content: Excel 文件内容
            created_by: 创建人ID

        Returns:
            处理结果
        """
        try:
            # 1. 解析 Excel
            logger.info(f"📊 开始解析 Excel 文件，大小: {len(file_content)} bytes")
            rows = self.parse_excel_to_jsonb(file_content)

            if not rows:
                raise ValueError("Excel 文件为空或格式不正确")

            logger.info(f"✅ Excel 解析成功: {len(rows)} 行, {len(rows[0]) if rows else 0} 列")

            # 2. 将该 knowledge_id 的旧数据置为失效状态（软删除）
            deactivate_query = sql_text(f"""
                UPDATE {global_schema}.knowledge_data
                SET status = :deleted_status
                WHERE knowledge_id = :knowledge_id
                    AND status = :active_status
            """)

            deactivated_result = self.db.execute(deactivate_query, {
                "deleted_status": KnowledgeStatusEnum.deleted.value,
                "knowledge_id": knowledge_id,
                "active_status": KnowledgeStatusEnum.active.value
            })

            deactivated_count = int(getattr(deactivated_result, 'rowcount', 0))
            if deactivated_count > 0:
                logger.info(f"🗑️  已将 {deactivated_count} 条旧数据置为失效状态")
                self.db.commit()  # 先提交删除操作

            # 3. 迭代每一行，保存为独立记录
            saved_records = []
            for idx, row_data in enumerate(rows, 1):
                try:
                    # 保存单行数据
                    knowledge_data = self.save_knowledge_data_row(
                        knowledge_id=knowledge_id,
                        row_data=row_data,
                        created_by=created_by
                    )
                    saved_records.append(knowledge_data)

                    # 为该行创建 FTS 索引
                    self.create_fts_index_for_row(knowledge_data)

                    # 每 2000 行提交一次，避免内存占用过大
                    if idx % 2000 == 0:
                        self.db.commit()
                        logger.info(f"  ✅ 已处理 {idx}/{len(rows)} 行")

                except Exception as e:
                    logger.error(f"❌ 处理第 {idx} 行失败: {e}")
                    # 单行失败不影响其他行
                    continue

            # 4. 最终提交剩余的记录
            self.db.commit()

            logger.info(f"✅ 数据保存并提交成功: 共保存 {len(saved_records)} 条记录")
            logger.info(f"📊 数据统计: 失效 {deactivated_count} 条旧数据，新增 {len(saved_records)} 条新数据")

            return {
                "status": "success",
                "knowledge_data_id": saved_records[0].id if saved_records else None,
                "rows_processed": len(saved_records),
                "columns": len(rows[0]) if rows else 0
            }

        except Exception as e:
            # ✅ 发生异常时回滚
            self.db.rollback()
            logger.error(f"❌ Excel 处理失败: {e}")
            raise

    def search_knowledge_data(
        self,
        knowledge_id: int,
        query: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        全文搜索知识数据（每行一条记录）

        Args:
            knowledge_id: 知识ID
            query: 搜索关键词
            top_n: 返回结果数量

        Returns:
            匹配的行数据
        """
        try:
            search_query = sql_text(f"""
                SELECT
                    id,
                    knowledge_id,
                    content,
                    ts_rank(fts_content, websearch_to_tsquery('zhparsercfg', :query)) AS rank_score
                FROM {global_schema}.knowledge_data
                WHERE
                    knowledge_id = :knowledge_id
                    AND fts_content @@ websearch_to_tsquery('zhparsercfg', :query)
                    AND status = 'active'
                ORDER BY rank_score DESC
                LIMIT :top_n
            """)

            result = self.db.execute(search_query, {
                "knowledge_id": knowledge_id,
                "query": query,
                "top_n": top_n
            })

            rows = result.fetchall()

            # 每条记录本身就是一行数据，直接返回
            results = []
            for row in rows:
                results.append({
                    "row": row.content,  # content 现在是单行数据对象
                    "score": float(row.rank_score),
                    "knowledge_data_id": row.id
                })

            logger.info(f"✅ 搜索完成: 找到 {len(results)} 条匹配记录")
            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            raise

    def search_knowledge_data_vector(
        self,
        knowledge_id: Optional[int],
        query: str,
        threshold: float = 0.7,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索知识数据

        Args:
            knowledge_id: 知识ID（可选，None 表示搜索所有）
            query: 搜索关键词
            threshold: 相似度阈值（0-1），默认0.7
            top_n: 返回结果数量

        Returns:
            匹配的行数据及相似度分数
        """
        try:
            # 1. 获取查询文本的向量
            query_embedding = get_text_embeddings_default(query)

            if not query_embedding:
                logger.error(f"❌ 查询文本向量化失败: {query}")
                return []

            # 2. 将向量转换为 PostgreSQL vector 格式
            vector_str = f'[{",".join(map(str, query_embedding))}]'

            # 3. 动态构建 SQL 条件
            if knowledge_id is not None:
                # 搜索指定 knowledge_id
                where_clause = "knowledge_id = :knowledge_id"
            else:
                # 搜索所有 knowledge_id
                where_clause = "1=1"

            # 4. 执行向量相似度搜索
            search_query = sql_text(f"""
                SELECT
                    id,
                    knowledge_id,
                    content,
                    1 - (fts_vector <=> :query_vector) AS similarity_score
                FROM {global_schema}.knowledge_data
                WHERE
                    {where_clause}
                    AND fts_vector IS NOT NULL
                    AND 1 - (fts_vector <=> :query_vector) >= :threshold
                    AND status = 'active'
                ORDER BY similarity_score DESC
                LIMIT :top_n
            """)

            params = {
                "query_vector": vector_str,
                "threshold": threshold,
                "top_n": top_n
            }
            if knowledge_id is not None:
                params["knowledge_id"] = knowledge_id

            result = self.db.execute(search_query, params)
            rows = result.fetchall()

            # 5. 格式化结果
            results = []
            for row in rows:
                results.append({
                    "row": row.content,
                    "score": float(row.similarity_score),
                    "knowledge_id": row.knowledge_id,  # 添加 knowledge_id
                    "knowledge_data_id": row.id
                })

            logger.info(f"✅ 向量搜索完成: 找到 {len(results)} 条匹配记录 (阈值={threshold})")
            return results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            raise
