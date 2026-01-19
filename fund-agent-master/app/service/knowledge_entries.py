from typing import List, Optional
from sqlalchemy import update, or_
from sqlalchemy.orm import Session

from app.model.knowledge import KnowledgeCatalog, Knowledge, KnowledgeDetail, KnowledgeTypeEnum, KnowledgeStatusEnum
from app.schema.knowledge import KnowledgeCatalogRead, KnowledgeRead, KnowledgeDetailRead
from app.schema.base import PageResponse
    
    
"""
    知识库内容的管理
"""

from app.model.knowledge import Knowledge, KnowledgeDetail
from app.schema.knowledge import KnowledgeRead,KnowledgeDetailRead,KnowledgeWithDetailsRead

class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db

    def create_knowledge(self,
                         knowledge_type: KnowledgeTypeEnum,
                         knowledge_catalog_id: int,
                         name: str,
                         status: KnowledgeStatusEnum = KnowledgeStatusEnum.pending,
                         created_by: Optional[int] = None) -> KnowledgeRead:
        """新建知识条目"""
        try:
            knowledge = Knowledge(
                knowledge_type=knowledge_type.value,  # 使用枚举的值
                knowledge_catalog_id=knowledge_catalog_id,
                name=name,
                status=status,  # 添加状态字段
                created_by=created_by
            )
            self.db.add(knowledge)
            self.db.commit()
            self.db.refresh(knowledge)
            return KnowledgeRead.model_validate(knowledge)
        except Exception as e:
            self.db.rollback()
            raise e

    def get_knowledges(self, knowledge_catalog_id: Optional[int] = None) -> List[KnowledgeRead]:
        """获取知识条目"""
        query = self.db.query(Knowledge)
        if knowledge_catalog_id is not None:
            query = query.filter(Knowledge.knowledge_catalog_id == knowledge_catalog_id,
                                 Knowledge.status == KnowledgeStatusEnum.active.value)
        else:
            query = query.filter(Knowledge.status == KnowledgeStatusEnum.active.value)
            
        result = query.all()
        return [KnowledgeRead.model_validate(knowledge) for knowledge in result]

    def update_knowledge(self,
                         id: int,
                         knowledge_type: KnowledgeTypeEnum,
                         knowledge_catalog_id: int,
                         status: KnowledgeStatusEnum,
                         name: str) -> KnowledgeRead:
        """更新知识条目"""
        try:
            knowledge = self.db.query(Knowledge).filter(Knowledge.id == id).first()
            if not knowledge:
                raise ValueError("Knowledge not found")

            stmt = (
                update(Knowledge)
                .where(Knowledge.id == id)
                .values(
                    knowledge_type=knowledge_type.value,
                    knowledge_catalog_id=knowledge_catalog_id,
                    name=name,
                    status=status.value
                )
            )
            self.db.execute(stmt)
            self.db.commit()
            self.db.refresh(knowledge)
            return KnowledgeRead.model_validate(knowledge)
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_knowledge(self, id: int) -> KnowledgeRead:
        """删除知识条目"""
        try:
            knowledge = self.db.query(Knowledge).filter(Knowledge.id == id).first()
            if not knowledge:
                raise ValueError("Knowledge not found")

            stmt = (
                update(Knowledge)
                .where(Knowledge.id == id)
                .values(status=KnowledgeStatusEnum.deleted.value)
            )
            self.db.execute(stmt)
            self.db.commit()
            self.db.refresh(knowledge)
            return KnowledgeRead.model_validate(knowledge)
        except Exception as e:
            self.db.rollback()
            raise e

    def create_knowledge_detail(self,
                                knowledge_id: int,
                                content: str,
                                reference: Optional[str],
                                role: str,
                                status: KnowledgeStatusEnum = KnowledgeStatusEnum.active,
                                created_by: Optional[int] = None) -> KnowledgeDetailRead:
        """新建答案条目"""
        try:
            # 先查询是否存在该知识条目
            knowledge = self.db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
            if not knowledge:
                raise ValueError("Knowledge not found")

            db_res = self.db.query(KnowledgeDetail).filter(
                KnowledgeDetail.knowledge_id == knowledge_id,
                KnowledgeDetail.status == KnowledgeStatusEnum.active.value
            ).order_by(KnowledgeDetail.version.desc()).first()

            version_no = 1
            if db_res:  # 如果已有版本，则递增版本号
                latest_detail = KnowledgeDetailRead.model_validate(db_res)
                version_no = latest_detail.version + 1

            # 创建详情
            detail = KnowledgeDetail(
                knowledge_id=knowledge_id,
                content=content,
                role=role,
                reference = reference,
                status=status.value,  # 使用枚举的值
                version=version_no,  # 默认初始版本为1
                created_by=created_by
            )

            self.db.add(detail)
            self.db.commit()
            self.db.refresh(detail)
            return KnowledgeDetailRead.model_validate(detail)
        except Exception as e:
            self.db.rollback()
            raise e

    def get_knowledge_details(self, knowledge_id: int) -> List[KnowledgeDetailRead]:
        """查询知识条目的所有详情"""
        result = self.db.query(KnowledgeDetail).filter(
            KnowledgeDetail.knowledge_id == knowledge_id,
            KnowledgeDetail.status != "deleted"
        ).order_by(KnowledgeDetail.version.desc()).all()
        return [KnowledgeDetailRead.model_validate(detail) for detail in result]

    def update_knowledge_detail(self, detail_id: int, content: str) -> KnowledgeDetailRead:
        """更新知识详情"""
        try:
            db_res = self.db.query(KnowledgeDetail).filter(KnowledgeDetail.id == detail_id).first()
            if not db_res:
                raise ValueError("Knowledge detail not found")

            stmt = (
                update(KnowledgeDetail)
                .where(KnowledgeDetail.id == detail_id)
                .values(content=content)
            )
            self.db.execute(stmt)
            self.db.commit()

            # 重新查询获取更新后的数据
            updated_detail = self.db.query(KnowledgeDetail).filter(KnowledgeDetail.id == detail_id).first()
            return KnowledgeDetailRead.model_validate(updated_detail)
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_knowledge_detail(self, knowledge_id: int) -> bool:
        """删除知识详情"""
        try:
            stmt = (
                update(KnowledgeDetail)
                .where(KnowledgeDetail.knowledge_id == knowledge_id)
                .values(status=KnowledgeStatusEnum.deleted.value)
            )

            self.db.execute(stmt)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_knowledge_by_type(self, knowledge_type: KnowledgeTypeEnum, page: int, size:int)-> PageResponse:
        """根据类型获取知识条目，分页"""
        total = 0
        if knowledge_type:  # 如果指定了知识目录ID，则只查询该目录下的知识条目
            query = self.db.query(Knowledge).filter(Knowledge.knowledge_type == knowledge_type.value).offset((page - 1) * size).limit(size)
            total = self.db.query(Knowledge).filter(Knowledge.knowledge_type == knowledge_type.value).count()
        else:  # 如果未指定知识目录ID，则查询所有知识条目
            query = self.db.query(Knowledge).offset((page - 1) * size).limit(size)
            total = self.db.query(Knowledge).count()

        items = [KnowledgeRead.model_validate(knowledge) for knowledge in query.all()]
        return PageResponse(items=items, total=total, page=page, size=size, has_next=total > page * size, has_prev=page > 1)
    def get_knowledge_by_catalog_id(self, knowledge_catalog_id, page: int, size: int )-> PageResponse:
        """根据类型获取知识条目，分页"""
        total = 0
        if knowledge_catalog_id:  # 如果指定了知识目录ID，则只查询该目录下的知识条目
            query = self.db.query(Knowledge).filter(Knowledge.knowledge_catalog_id == knowledge_catalog_id).offset((page - 1) * size).limit(size)
            total = self.db.query(Knowledge).filter(Knowledge.knowledge_catalog_id == knowledge_catalog_id).count()
        else:  # 如果未指定知识目录ID，则查询所有知识条目
            query = self.db.query(Knowledge).offset((page - 1) * size).limit(size)
            total = self.db.query(Knowledge).count()

        items = [KnowledgeRead.model_validate(knowledge) for knowledge in query.all()]
        return PageResponse(items=items, 
                            total=total, 
                            page=page, 
                            size=size, 
                            has_next=total > page * size, 
                            has_prev=page > 1)
    

    
    def search_knowledges(self,
                        knowledge_catalog_id: List[int] =[],
                        knowledge_type: Optional[KnowledgeTypeEnum] = None,
                        knowledge_status: Optional[str] = None,
                        name: Optional[str] = None,
                        orderby: str = "id",
                        order: str = "desc",
                        page: int = 1,
                        size: int = 10) -> PageResponse:
        """
        搜索知识条目（支持分页和多条件查询）

        Args:
            knowledge_catalog_id: 知识目录ID列表
            knowledge_type: 知识类型
            knowledge_status: 知识状态
            name: 知识名称（模糊匹配）
            orderby: 排序字段，支持 'id', 'created_at', 'updated_at'，默认为 'id'
            order: 排序方向，支持 'asc' 或 'desc'，默认为 'desc'
            page: 页码（从1开始）
            size: 每页大小

        Returns:
            分页结果字典
        """
        
        # 构建查询，同时 LEFT JOIN KnowledgeCatalog
        query = self.db.query(
            Knowledge,
            KnowledgeCatalog,
            KnowledgeDetail
        ).filter(
            Knowledge.status != KnowledgeStatusEnum.deleted
        ).outerjoin(
            KnowledgeCatalog,
            Knowledge.knowledge_catalog_id == KnowledgeCatalog.id
        ).outerjoin(
            KnowledgeDetail,
            Knowledge.id == KnowledgeDetail.knowledge_id,
        ).filter(
            or_(
                KnowledgeDetail.id == None,
                KnowledgeDetail.version == self.db.query(
                    KnowledgeDetail.version
                ).filter(
                    KnowledgeDetail.knowledge_id == Knowledge.id,
                    KnowledgeDetail.status != KnowledgeStatusEnum.deleted.value
                ).order_by(
                    KnowledgeDetail.version.desc()
                ).limit(1).correlate(Knowledge).scalar_subquery()
            ),
            KnowledgeDetail.status != KnowledgeStatusEnum.deleted.value
        )
        
        # 添加过滤条件
        if len(knowledge_catalog_id)>0:
            query = query.filter(Knowledge.knowledge_catalog_id.in_(knowledge_catalog_id))
            
        if knowledge_type is not None:
            query = query.filter(Knowledge.knowledge_type == knowledge_type)

        if knowledge_status is not None and knowledge_status!='all':
            query = query.filter(Knowledge.status == knowledge_status)
        
            
        if name:
            try:
                # 尝试将 name 转换为整数进行 ID 匹配
                name_int = int(name)
                query = query.filter(
                    or_(Knowledge.name.contains(name),
                        Knowledge.id == name_int
                        )
                )
            except ValueError:
                # 如果无法转换为整数，只匹配名称
                query = query.filter(
                    or_(Knowledge.name.contains(name),
                        KnowledgeDetail.filled_by.contains(name),
                        KnowledgeDetail.content.contains(name)
                        )
                    )
        
        
        # 计算总数
        total = query.count()

        # 验证排序字段，防止SQL注入
        valid_orderby_fields = {
            'id': Knowledge.id,
            'created_at': Knowledge.created_at,
            'updated_at': Knowledge.updated_at
        }

        # 获取排序字段，默认使用 id，无效值则使用默认值
        order_field = valid_orderby_fields.get(orderby, Knowledge.id)

        # 验证排序方向，防止非法值
        order_direction = order.lower() if order in ['asc', 'desc'] else 'desc'

        # 应用分页和排序（动态选择升序或降序）
        offset = (page - 1) * size
        if order_direction == 'asc':
            results = query.order_by(order_field.asc()).offset(offset).limit(size).all()
        else:
            results = query.order_by(order_field.desc()).offset(offset).limit(size).all()
        # 转换为包含详情和目录信息的完整对象
        knowledge_with_details_list = []
        for knowledge, catalog, detail in results:
            knowledge_read = KnowledgeRead.model_validate(knowledge)
            
            # 获取关联的详情
            details = None
            if detail:
                details = KnowledgeDetailRead.model_validate(detail)
            
            # 获取关联的目录信息
            catalog_info = None
            if catalog:
                catalog_info = KnowledgeCatalogRead.model_validate(catalog)

            res = KnowledgeWithDetailsRead(
                id=knowledge_read.id,
                created_at=knowledge_read.created_at,
                updated_at=knowledge_read.updated_at,
                knowledge_catalog_id=knowledge_read.knowledge_catalog_id,
                knowledge_type=knowledge_read.knowledge_type,
                name=knowledge_read.name,
                status=knowledge_read.status,
                details=details,
                catalog=catalog_info)
            knowledge_with_details_list.append(res)

        # 构造分页信息
        has_next = page * size < total
        has_prev = page > 1
        
        return PageResponse(items=knowledge_with_details_list, 
                            total=total, 
                            page=page, 
                            size=size, 
                            has_next=has_next, 
                            has_prev=has_prev)
        