from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import text as sql_text
import pandas as pd
import logging
from io import BytesIO

from app.model.knowledge import KnowledgeData, KnowledgeStatusEnum

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
        为单行数据创建全文搜索索引

        Args:
            knowledge_data: KnowledgeData 实例

        Returns:
            是否成功
        """
        try:
            # 提取该行数据的所有文本
            row_text = " ".join(
                str(v).strip()
                for v in knowledge_data.content.values()
                if v is not None and str(v).strip()
            )
            logger.info(f'row_text:\n{row_text}')

            # ✅ 空文本检查
            if not row_text:
                logger.warning(f"⚠️ 行数据 {knowledge_data.id} 没有可索引的文本内容")
                return True

            # 更新 FTS 索引（使用 UPDATE 语句）
            update_query = sql_text("""
                UPDATE housing_fund.knowledge_data
                SET fts_content = to_tsvector('zhparsercfg', :text_content)
                WHERE id = :knowledge_data_id
            """)

            self.db.execute(update_query, {
                "knowledge_data_id": knowledge_data.id,
                "text_content": row_text
            })

            return True

        except Exception as e:
            logger.error(f"❌ FTS 索引创建失败 (ID: {knowledge_data.id}): {e}")
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
            deactivate_query = sql_text("""
                UPDATE housing_fund.knowledge_data
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
            search_query = sql_text("""
                SELECT
                    id,
                    knowledge_id,
                    content,
                    ts_rank(fts_content, websearch_to_tsquery('zhparsercfg', :query)) AS rank_score
                FROM housing_fund.knowledge_data
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
