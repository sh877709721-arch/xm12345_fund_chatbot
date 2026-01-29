from fastapi import Depends
from typing import List, Optional
from fastapi import Depends
from sqlalchemy import select,update, or_,and_
from sqlalchemy.orm import Session

"""
    知识目录管理

"""
from app.model.knowledge import KnowledgeCatalog, Knowledge, KnowledgeDetail, KnowledgeTypeEnum, KnowledgeStatusEnum
from app.schema.knowledge import KnowledgeCatalogRead, KnowledgeRead, KnowledgeDetailRead
from app.schema.base import PageResponse, BaseResponse
from typing import Dict, Any

class KnowledgeCatalogService:
    def __init__(self, db: Session):
        self.db = db

    def create_knowledge_catalog(self,
                                 catalog_level_1: str,
                                 catalog_level_2: str,
                                 catalog_level_3: str):
        """创建知识目录"""
        try:
            knowledge_catalog = KnowledgeCatalog(
                category_level_1=catalog_level_1,
                category_level_2=catalog_level_2,
                category_level_3=catalog_level_3,
                status=KnowledgeStatusEnum.active.value  # 使用枚举的值
            )
            self.db.add(knowledge_catalog)
            self.db.commit()
            self.db.refresh(knowledge_catalog)
            return KnowledgeCatalogRead.model_validate(knowledge_catalog)
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_knowledge_catalogs(self) -> List[KnowledgeCatalogRead]:
        """获取所有知识目录"""

        result = self.db.query(KnowledgeCatalog).where(KnowledgeCatalog.status==KnowledgeStatusEnum.active).all()
        return [KnowledgeCatalogRead.model_validate(knowledge_catalog) for knowledge_catalog in result]
    
    # 根据
    def get_knowledge_catalog_by_level(self,
                                       level_1: str| None,
                                       level_2: str| None,
                                       level_3: str| None
                                       )-> List[KnowledgeCatalogRead]:
        """根据级别获取知识目录 - 支持部分层级匹配"""
        # 构建查询条件
        conditions = [KnowledgeCatalog.status == KnowledgeStatusEnum.active.value]

        # 只有当参数不为 None 时才添加到查询条件中
        if level_1 is not None:
            conditions.append(KnowledgeCatalog.category_level_1 == level_1)
        if level_2 is not None:
            conditions.append(KnowledgeCatalog.category_level_2 == level_2)
        if level_3 is not None:
            conditions.append(KnowledgeCatalog.category_level_3 == level_3)

        # 使用 and_ 连接所有条件
        result = self.db.query(KnowledgeCatalog).where(and_(*conditions)).all()

        if result:
            return [KnowledgeCatalogRead.model_validate(knowledge_catalog) for knowledge_catalog in result]
        return []

    
    def get_knowledge_catalog_tree(self) -> List[Dict[str, Any]]:
        """获取树形结构的知识目录"""
        result = self.db.query(KnowledgeCatalog).where(KnowledgeCatalog.status == KnowledgeStatusEnum.active.value).all()
        
        # 构建树形结构
        tree = {}
        for catalog in result:
            # 跳过已删除的目录
                
            level_1 = catalog.category_level_1 or "未分类"
            level_2 = catalog.category_level_2 or "未分类"
            level_3 = catalog.category_level_3 or "未分类"
            
            # 创建第一层
            if level_1 not in tree:
                tree[level_1] = {}
            
            # 创建第二层
            if level_2 not in tree[level_1]:
                tree[level_1][level_2] = []

            # 添加目录项
            tree[level_1][level_2].append({
                "id": catalog.id,
                "name": catalog.category_level_3,
            })
        
        return [tree]

    def update_knowledge_catalog(self, id: int,
                                 catalog_level_1: str,
                                 catalog_level_2: str,
                                 catalog_level_3: str):
        """更新知识目录"""
        try:
            knowledge_catalog = self.db.query(KnowledgeCatalog).filter(KnowledgeCatalog.id == id).first()
            if not knowledge_catalog:
                raise ValueError("Knowledge catalog not found")

            # 更新现有对象的属性
            stmt = (
                update(KnowledgeCatalog)
                .where(KnowledgeCatalog.id == id)
                .values(
                    category_level_1=catalog_level_1,
                    category_level_2=catalog_level_2,
                    category_level_3=catalog_level_3
                ))
            self.db.execute(stmt)
            self.db.commit()
            self.db.refresh(knowledge_catalog)
            return KnowledgeCatalogRead.model_validate(knowledge_catalog)
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_knowledge_catalog(self, id: int):
        """删除知识目录"""
        try:
            knowledge_catalog = self.db.query(KnowledgeCatalog).filter(KnowledgeCatalog.id == id).first()
            if not knowledge_catalog:
                raise ValueError("Knowledge catalog not found")
            stmt = (
                update(KnowledgeCatalog)
                .where(KnowledgeCatalog.id == id)
                .values(status=KnowledgeStatusEnum.deleted.value)  # 使用枚举的值
            )
            self.db.execute(stmt)
            self.db.commit()
            self.db.refresh(knowledge_catalog)
            return KnowledgeCatalogRead.model_validate(knowledge_catalog)
        except Exception as e:
            self.db.rollback()
            raise e
    