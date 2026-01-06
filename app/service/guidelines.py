from typing import List, Optional
import logging
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.model.guidelines import Guidelines
from app.schema.guideline import (
    GuidelinesRead,
    GuidelinesCreate,
    GuidelinesUpdate,
    GuidelinesStatusEnum
)
from app.schema.base import PageResponse
from app.config.llm_client import embedding_client

logger = logging.getLogger(__name__)


# 配置
BATCH_SIZE = 2
MODEL_NAME = "bge-m3"
EMBEDDING_DIM = 1024

class GuidelinesService:
    """指南管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_guideline(self,
                         title: str,
                         condition: str,
                         action: str,
                         prompt_template: Optional[str] = None,
                         status: str = GuidelinesStatusEnum.draft.value) -> GuidelinesRead:
        """
        创建指南

        Args:
            title: 指南标题
            condition: 触发条件
            action: 执行动作
            prompt_template: 提示词模板
            status: 状态

        Returns:
            创建的指南对象
        """
        try:
            guideline = Guidelines(
                title=title,
                condition=condition,
                action=action,
                prompt_template=prompt_template,
                status=status
            )
            self.db.add(guideline)
            self.db.commit()
            self.db.refresh(guideline)
            logger.info(f"Created guideline with id: {guideline.id}")
            return GuidelinesRead.model_validate(guideline)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create guideline: {e}")
            raise e

    def get_guideline(self, guideline_id: int) -> Optional[GuidelinesRead]:
        """
        获取单个指南

        Args:
            guideline_id: 指南ID

        Returns:
            指南对象或None
        """
        guideline = self.db.query(Guidelines).filter(
            Guidelines.id == guideline_id,
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        ).first()

        if guideline:
            return GuidelinesRead.model_validate(guideline)
        return None

    def get_guidelines(self) -> List[GuidelinesRead]:
        """
        获取所有未删除的指南

        Returns:
            指南列表
        """
        guidelines = self.db.query(Guidelines).filter(
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        ).order_by(Guidelines.id.desc()).all()

        return [GuidelinesRead.model_validate(g) for g in guidelines]
    
    def get_guidelines_by_id(self, guideline_id: int):
        """
        获取所有未删除的指南
        """
        guideline = self.db.query(Guidelines).filter(
            Guidelines.id == id,
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        )
        return guideline

    def update_guideline(self,
                         guideline_id: int,
                         title: Optional[str] = None,
                         condition: Optional[str] = None,
                         action: Optional[str] = None,
                         prompt_template: Optional[str] = None,
                         status: Optional[str] = None) -> GuidelinesRead:
        """
        更新指南

        Args:
            guideline_id: 指南ID
            title: 标题
            condition: 条件
            action: 动作
            prompt_template: 提示词模板
            status: 状态

        Returns:
            更新后的指南对象
        """
        try:
            guideline = self.db.query(Guidelines).filter(
                Guidelines.id == guideline_id
            ).first()

            if not guideline:
                raise ValueError(f"Guideline with id {guideline_id} not found")

            # 构建更新字典
            update_values = {}
            if title is not None:
                update_values['title'] = title
            if condition is not None:
                update_values['condition'] = condition
            if action is not None:
                update_values['action'] = action
            if prompt_template is not None:
                update_values['prompt_template'] = prompt_template
            if status is not None:
                update_values['status'] = status

            if update_values:
                stmt = (
                    update(Guidelines)
                    .where(Guidelines.id == guideline_id)
                    .values(**update_values)
                )
                self.db.execute(stmt)
                self.db.commit()
                self.db.refresh(guideline)
                logger.info(f"Updated guideline with id: {guideline_id}")

            return GuidelinesRead.model_validate(guideline)
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update guideline {guideline_id}: {e}")
            raise e

    def delete_guideline(self, guideline_id: int) -> GuidelinesRead:
        """
        删除指南（软删除）

        Args:
            guideline_id: 指南ID

        Returns:
            被删除的指南对象
        """
        try:
            guideline = self.db.query(Guidelines).filter(
                Guidelines.id == guideline_id
            ).first()

            if not guideline:
                raise ValueError(f"Guideline with id {guideline_id} not found")

            stmt = (
                update(Guidelines)
                .where(Guidelines.id == guideline_id)
                .values(status=GuidelinesStatusEnum.deleted.value)
            )
            self.db.execute(stmt)
            self.db.commit()
            self.db.refresh(guideline)
            logger.info(f"Deleted guideline with id: {guideline_id}")

            return GuidelinesRead.model_validate(guideline)
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete guideline {guideline_id}: {e}")
            raise e

    def search_guidelines(self,
                          title: Optional[str] = None,
                          condition: Optional[str] = None,
                          action: Optional[str] = None,
                          status: Optional[str] = None,
                          page: int = 1,
                          size: int = 10) -> PageResponse:
        """
        搜索指南（支持分页和多条件查询）

        Args:
            title: 标题（模糊匹配）
            condition: 条件（模糊匹配）
            action: 动作（模糊匹配）
            status: 状态（精确匹配）
            page: 页码（从1开始）
            size: 每页大小

        Returns:
            分页结果
        """
        # 构建查询
        query = self.db.query(Guidelines).filter(
            Guidelines.status != GuidelinesStatusEnum.deleted.value
        )

        # 添加过滤条件
        if title:
            query = query.filter(Guidelines.title.contains(title))

        if condition:
            query = query.filter(Guidelines.condition.contains(condition))

        if action:
            query = query.filter(Guidelines.action.contains(action))

        if status:
            query = query.filter(Guidelines.status == status)

        # 计算总数
        total = query.count()

        # 应用分页
        offset = (page - 1) * size
        paginated_query = query.order_by(Guidelines.id.desc()).offset(offset).limit(size)

        results = paginated_query.all()
        items = [GuidelinesRead.model_validate(guideline) for guideline in results]

        # 构造分页信息
        has_next = page * size < total
        has_prev = page > 1

        return PageResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            has_next=has_next,
            has_prev=has_prev
        )


    def _generate_embeddings(self,texts: List[str]) -> List[List[float]]:
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

    def build_index_by_guideline_id(self, guideline_id):
        """构建向量索引"""
        try:
            # 获取指南内容
            guideline = self.db.query(Guidelines).filter(
                Guidelines.id == guideline_id,
                Guidelines.status != GuidelinesStatusEnum.deleted.value
            ).first()
            
            guideline_read = GuidelinesRead.model_validate(guideline)

            if not guideline:
                raise ValueError(f"指南 {guideline_id} 不存在")
            
            
            # 构建索引项
            emb = self._generate_embeddings([guideline_read.condition])[0]
            guideline.condition_embedding = emb
            guideline.set_condition_fts()
            self.db.commit()
    
        except Exception as e:
            error_msg = f"Failed to build index for guideline {guideline_id}: {str(e)}"
            raise Exception(error_msg)