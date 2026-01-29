from fastapi import Depends
from typing import List, Optional
from fastapi import Depends
from sqlalchemy import select,update, or_
from sqlalchemy.orm import Session

"""
    知识测试及标注
"""
from app.model.knowledge import Knowledge, KnowledgeTypeEnum, KnowledgeStatusEnum,KnoewledgeRoleEnum
from app.model.knowledge_label import KnowledgeLabel, KnowledgeLabelBatch, KnowledgeLabelDetail
from app.schema.knowledge import (
    KnowledgeLabelBatchRead,
    KnowledgeLabelRead,
    KnowledgeLabelDetailRead,
    KnowledgeLabelWithDetailRead,
    PassStateEnum
)
from app.schema.base import BaseResponse, PageResponse

from sqlalchemy import func, and_
from sqlalchemy.orm import aliased, Session
from datetime import datetime
import math


class KnowledgeLabelService:
    def __init__(self, db: Session):
        self.db = db

    # 新建知识标注测试批次
    def create_knowledge_label_batch(self, name: str) -> KnowledgeLabelBatchRead:
        try:
            knowledge_label_batch = KnowledgeLabelBatch(name=name)
            self.db.add(knowledge_label_batch)
            self.db.commit()
            self.db.refresh(knowledge_label_batch)
            return KnowledgeLabelBatchRead.model_validate(knowledge_label_batch)
        except Exception as e:
            self.db.rollback()
            raise e
    

        # 获取知识标注批次
    def get_knowledge_label_batch(self, batch_id:int ) -> List[KnowledgeLabelBatchRead]:
        knowledge_label_batch = self.db.query(KnowledgeLabelBatch).filter(
            KnowledgeLabelBatch.id == batch_id,
            KnowledgeLabelBatch.status!=KnowledgeStatusEnum.deleted).all()
        return [KnowledgeLabelBatchRead.model_validate(knowledge_label_batch) for knowledge_label_batch in knowledge_label_batch]
    

    # 获取知识标注批次
    def get_knowledge_label_batchs(self) -> List[KnowledgeLabelBatchRead]:
        knowledge_label_batch = self.db.query(KnowledgeLabelBatch).filter(
            KnowledgeLabelBatch.status!=KnowledgeStatusEnum.deleted
            ).order_by(KnowledgeLabelBatch.id.desc()).all()
        return [KnowledgeLabelBatchRead.model_validate(knowledge_label_batch) for knowledge_label_batch in knowledge_label_batch]
    

    # 更新批次
    def update_knowledge_label_batch(self, id: int, name: str) -> KnowledgeLabelBatchRead:
        try:
            knowledge_label_batch = self.db.query(KnowledgeLabelBatch).filter(
                KnowledgeLabelBatch.id == id
                ).first()
            if not knowledge_label_batch:
                raise Exception("批次不存在")
            knowledge_label_batch.set_name(name)
            self.db.add(knowledge_label_batch)
            self.db.commit()
            self.db.refresh(knowledge_label_batch)
            return KnowledgeLabelBatchRead.model_validate(knowledge_label_batch)
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_knowledge_label_batch(self, id: int) -> bool:
        try:
            knowledge_label_batch = self.db.query(KnowledgeLabelBatch).filter(
                KnowledgeLabelBatch.id == id).first()
            if not knowledge_label_batch:
                raise Exception("批次不存在")
            
            # 1. 软删除批次
            knowledge_label_batch.set_status(KnowledgeStatusEnum.deleted.value)
            self.db.add(knowledge_label_batch)
            
            # 2. 批量软删除 KnowledgeLabel
            self.db.query(KnowledgeLabel).filter(
                KnowledgeLabel.batch_id == id
            ).update({
                KnowledgeLabel.status: KnowledgeStatusEnum.deleted.value,
                KnowledgeLabel.updated_at: datetime.now()
            }, synchronize_session=False)
            
            # 3. 获取该批次下所有 KnowledgeLabel ID
            label_ids = [label.id for label in self.db.query(KnowledgeLabel).filter(
                KnowledgeLabel.batch_id == id).all()]
            
            if label_ids:
                # 4. 批量软删除 KnowledgeLabelDetail
                self.db.query(KnowledgeLabelDetail).filter(
                    KnowledgeLabelDetail.knowledge_label_id.in_(label_ids)
                ).update({
                    KnowledgeLabelDetail.status: KnowledgeStatusEnum.deleted.value,
                    KnowledgeLabelDetail.updated_at:datetime.now()
                }, synchronize_session=False)
            
            self.db.commit()
            self.db.refresh(knowledge_label_batch)
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    # 创建知识标注条目
    def create_knowledge_label(self, knowledge_label_batch_id: int, name: str) -> KnowledgeLabelRead:
        try:
            # 验证批次存在
            knowledge_label_batch = self.db.query(KnowledgeLabelBatch).filter(
                KnowledgeLabelBatch.id == knowledge_label_batch_id).first()
            if not knowledge_label_batch:
                raise Exception("批次不存在")
            knowledge_label = KnowledgeLabel(batch_id=knowledge_label_batch_id,
                                             name=name,
                                             status=KnowledgeStatusEnum.active.value
                                             )
            self.db.add(knowledge_label)
            self.db.commit()
            self.db.refresh(knowledge_label)
            return KnowledgeLabelRead.model_validate(knowledge_label)
        except Exception as e:
            self.db.rollback()
            raise e
    # 批量新增知识标注条目
    def create_knowledge_labels(self, knowledge_label_batch_id: int, name: List[str]) -> dict:
        try:
            knowledge_labels = [
                KnowledgeLabel(batch_id=knowledge_label_batch_id, name=label_name)
                for label_name in name
            ]
            self.db.add_all(knowledge_labels)
            self.db.commit()
            # 批量操作后不需要refresh单个对象
            return {"message": "创建成功"}
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_knowledge_label(self, id: int) -> List[KnowledgeLabelRead]:
        knowledge_label = self.db.query(KnowledgeLabel).filter(
            KnowledgeLabel.id == id).all()
        return [KnowledgeLabelRead.model_validate(knowledge_label) for knowledge_label in knowledge_label]
    

    def get_knowledge_label_pagination(self, 
                                       page: int = 1, 
                                       size: int = 10) -> PageResponse[KnowledgeLabelRead]:
        knowledge_label = self.db.query(KnowledgeLabel).filter(
            KnowledgeLabel.status!=KnowledgeStatusEnum.deleted
            ).order_by(KnowledgeLabel.id.desc()).offset((page - 1) * size).limit(size).all()
        total = self.db.query(KnowledgeLabel).filter(
            KnowledgeLabel.status!=KnowledgeStatusEnum.deleted
            ).count()
        
        return PageResponse(items=[KnowledgeLabelRead.model_validate(knowledge_label) for knowledge_label in knowledge_label],
                            total=total,
                            page=page,
                            size=size,
                            has_next=total > page * size,
                            has_prev=page > 1)

    

        # 创建知识标注详情
    def create_knowledge_label_detail(self,
                                      label_id:int,
                                      content:Optional[str],
                                      context:str,
                                      role:str,
                                      status:KnowledgeStatusEnum,
                                      is_pass:Optional[bool],
                                      description:Optional[str],
                                      filled_by:Optional[str],
                                      ) -> KnowledgeLabelDetailRead:
        try:
            # 查询version最大的记录
            knowledge_label_detail = self.db.query(KnowledgeLabelDetail).filter(
                KnowledgeLabelDetail.knowledge_label_id == label_id,
                KnowledgeLabelDetail.status!=KnowledgeStatusEnum.deleted,
                KnowledgeLabelDetail.role == role
                ).order_by(KnowledgeLabelDetail.version.desc()).first()
            version_no = 1
            if knowledge_label_detail:
                version_no = knowledge_label_detail.version + 1
                knowledge_label_detail.set_state(KnowledgeStatusEnum.deleted)
                self.db.add(knowledge_label_detail)
                # 这里不立即commit，等整个操作完成后再一起提交

            # 创建新记录
            new_knowledge_label_detail = KnowledgeLabelDetail(
                knowledge_label_id = label_id,
                content=content,
                context=context,
                role=role,
                status=status,
                is_pass=is_pass,
                filled_by=filled_by,
                description=description,
                version=version_no
            )
            self.db.add(new_knowledge_label_detail)
            self.db.commit()
            self.db.refresh(new_knowledge_label_detail)
            return KnowledgeLabelDetailRead.model_validate(new_knowledge_label_detail)
        except Exception as e:
            self.db.rollback()
            raise e

    # 创建知识标注详情
    def create_knowledge_label_with_detail(self,
                                      label_id:int,
                                      content:Optional[str],
                                      context:str,
                                      role:str,
                                      status:KnowledgeStatusEnum,
                                      is_pass:Optional[bool],
                                      description:Optional[str],
                                      filled_by:Optional[str],
                                      ) -> KnowledgeLabelDetailRead:
        try:
            # 查询version最大的记录
            knowledge_label_detail = self.db.query(KnowledgeLabelDetail).filter(
                KnowledgeLabelDetail.knowledge_label_id == label_id,
                KnowledgeLabelDetail.status!=KnowledgeStatusEnum.deleted,
                KnowledgeLabelDetail.role == role
                ).order_by(KnowledgeLabelDetail.version.desc()).first()
            version_no = 1
            if knowledge_label_detail:
                version_no = knowledge_label_detail.version + 1
                knowledge_label_detail.set_state(KnowledgeStatusEnum.deleted)
                self.db.add(knowledge_label_detail)
                # 这里不立即commit，等整个操作完成后再一起提交

            # 创建新记录
            new_knowledge_label_detail = KnowledgeLabelDetail(
                knowledge_label_id = label_id,
                content=content,
                context=context,
                role=role,
                status=status,
                is_pass=is_pass,
                filled_by=filled_by,
                description=description,
                version=version_no
            )
            self.db.add(new_knowledge_label_detail)
            self.db.commit()
            self.db.refresh(new_knowledge_label_detail)
            return KnowledgeLabelDetailRead.model_validate(new_knowledge_label_detail)
        except Exception as e:
            self.db.rollback()
            raise e
    
    # 修改知识条目
    def update_knowledge_label(self, id: int, name: str) -> KnowledgeLabelRead:
        try:
            knowledge_label = self.db.query(KnowledgeLabel).filter(KnowledgeLabel.id == id).first()
            if not knowledge_label:
                raise Exception("条目不存在")
            knowledge_label.set_name(name)
            self.db.add(knowledge_label)
            self.db.commit()
            self.db.refresh(knowledge_label)
            return KnowledgeLabelRead.model_validate(knowledge_label)
        except Exception as e:
            self.db.rollback()
            raise e
    
    # 修改知识明细
    def update_knowledge_label_detail(self,
                                      detail_id:int,
                                      content:str,
                                      context:str,
                                      role:str,
                                      status:KnowledgeStatusEnum,
                                      is_pass:bool,
                                      description:str,
                                      filled_by:str,
                                      ) -> KnowledgeLabelDetailRead:
        try:
            # 查询version最大的记录
            knowledge_label_detail = self.db.query(KnowledgeLabelDetail).filter(KnowledgeLabelDetail.id == detail_id).order_by(KnowledgeLabelDetail.version.desc()).first()
            version_no = 1
            old_knowledge_label_id = None
            if knowledge_label_detail:
                version_no = knowledge_label_detail.version + 1
                old_knowledge_label_id = knowledge_label_detail.knowledge_label_id
                knowledge_label_detail.set_state(KnowledgeStatusEnum.deleted)
                self.db.add(knowledge_label_detail)
                # 这里不立即commit，等整个操作完成后再一起提交

            # 创建新记录
            new_knowledge_label_detail = KnowledgeLabelDetail(id=detail_id,
                                                            knowledge_label_id=old_knowledge_label_id,
                                                            content=content,
                                                            context=context,
                                                            role=role, status=status,
                                                            is_pass=is_pass,
                                                            filled_by=filled_by,
                                                            description=description,
                                                            version=version_no)
            self.db.add(new_knowledge_label_detail)
            self.db.commit()
            self.db.refresh(new_knowledge_label_detail)
            return KnowledgeLabelDetailRead.model_validate(new_knowledge_label_detail)
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_knowledge_label_detail(self, detail_id: int) -> dict:
        try:
            knowledge_label_detail = self.db.query(KnowledgeLabelDetail).filter(KnowledgeLabelDetail.id == detail_id).first()
            if not knowledge_label_detail:
                raise Exception("条目不存在")
            knowledge_label_detail.set_state(KnowledgeStatusEnum.deleted)
            self.db.add(knowledge_label_detail)
            self.db.commit()
            return {"message": "删除成功"}
        except Exception as e:
            self.db.rollback()
            raise e

    def query_knowledge_labels_details(self, 
                                       batch_id, 
                                       name, 
                                       pass_state,
                                       filled_by,
                                       page, 
                                       size) -> PageResponse[KnowledgeLabelWithDetailRead]:
        
        # 创建两个别名，分别用于user和assistant的最新记录
        user_detail_alias = aliased(KnowledgeLabelDetail)
        assistant_detail_alias = aliased(KnowledgeLabelDetail)
        
        # 子查询1：获取每个KnowledgeLabel_id下role='user'的最新版本记录
        user_latest_subq = (
            self.db.query(
                KnowledgeLabelDetail.knowledge_label_id,
                func.max(KnowledgeLabelDetail.version).label('max_version')
            )
            .filter(KnowledgeLabelDetail.role == KnoewledgeRoleEnum.user,
                    KnowledgeLabelDetail.status != KnowledgeStatusEnum.deleted)
            .group_by(KnowledgeLabelDetail.knowledge_label_id)
            .subquery('user_latest')
        )
        
        # 子查询2：获取每个KnowledgeLabel_id下role='assistant'的最新版本记录
        assistant_latest_subq = (
            self.db.query(
                KnowledgeLabelDetail.knowledge_label_id,
                func.max(KnowledgeLabelDetail.version).label('max_version')
            )
            .filter(KnowledgeLabelDetail.role == KnoewledgeRoleEnum.assistant,
                    KnowledgeLabelDetail.status != KnowledgeStatusEnum.deleted)
            .group_by(KnowledgeLabelDetail.knowledge_label_id)
            .subquery('assistant_latest')
        )
        # 主查询：只查询当前页的KnowledgeLabel ID对应的详情
        query = (
            self.db.query(
                KnowledgeLabel.batch_id.label('batch_number'),
                KnowledgeLabel.id.label('label_id'),
                KnowledgeLabel.name.label('question'),
                assistant_detail_alias.content.label('ai_content'),       # AI内容
                user_detail_alias.content.label('user_content'),          # 用户内容   
                user_detail_alias.is_pass.label('is_passed'),             # 是否通过
                user_detail_alias.description.label('description'),       # 原因
                user_detail_alias.filled_by.label('filled_by'),           # 整理人
                KnowledgeLabel.created_at.label('create_time'),           # 时间
                KnowledgeLabel.updated_at.label('update_time'),
            )
            .outerjoin(user_detail_alias, and_(
                KnowledgeLabel.id == user_detail_alias.knowledge_label_id,
                user_detail_alias.role == KnoewledgeRoleEnum.user,
                user_detail_alias.status != KnowledgeStatusEnum.deleted
                ))
            .outerjoin(assistant_detail_alias,and_(
                KnowledgeLabel.id == assistant_detail_alias.knowledge_label_id,
                assistant_detail_alias.role == KnoewledgeRoleEnum.assistant,
                assistant_detail_alias.status != KnowledgeStatusEnum.deleted
                ))
            # .outerjoin(user_latest_subq, 
            #     and_(user_detail_alias.knowledge_label_id == user_latest_subq.c.knowledge_label_id,
            #         user_detail_alias.version == user_latest_subq.c.max_version))
            # .outerjoin(assistant_latest_subq, 
            #     and_(assistant_detail_alias.knowledge_label_id == assistant_latest_subq.c.knowledge_label_id,
            #         assistant_detail_alias.version == assistant_latest_subq.c.max_version))
            .filter(KnowledgeLabel.status != KnowledgeStatusEnum.deleted)
            .filter(KnowledgeLabel.batch_id == batch_id)
            .order_by(KnowledgeLabel.id.desc())
        )

        

        if len(name)>0:
            query = query.filter(KnowledgeLabel.name.contains(name))

        if len(filled_by)>0:
            query = query.where(user_detail_alias.filled_by.contains(filled_by))

        #import pdb; pdb.set_trace()
        if pass_state == PassStateEnum.passed:
            query = query.filter(user_detail_alias.is_pass == True)
        elif pass_state == PassStateEnum.unchecked:
            query = query.filter(user_detail_alias.is_pass.is_(None))
        elif pass_state == PassStateEnum.unpassed:
            query = query.filter(user_detail_alias.is_pass == False)
        

        total = query.count()
        # 分页
        query = query.offset((page - 1) * size).limit(size)


        # 执行查询
        results = query.all()
        
        # 转换为需要的格式
        items = []
        for row in results:
            item = {
                "batch_number": row.batch_number,
                "label_id": row.label_id,
                "question": row.question,
                "ai_content": row.ai_content,
                "user_content": row.user_content,
                "is_passed": row.is_passed,
                "description": row.description,
                "filled_by": row.filled_by,
                "create_at": row.create_time,
                "update_at": row.update_time
            }
            items.append(item)
        
        # 计算总页数
        total_pages = math.ceil(total / size) if size else 1
        
        return PageResponse[KnowledgeLabelWithDetailRead](
            total=total,
            page=page,
            size=size,
            items=items,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    def query_knowledge_labels_details_old(self, 
                                       batch_id, 
                                       filled_state,
                                       filled_by,
                                       name, 
                                       page, 
                                       size) -> PageResponse[KnowledgeLabelWithDetailRead]:
        
        # 创建两个别名，分别用于user和assistant的最新记录
        user_detail_alias = aliased(KnowledgeLabelDetail)
        assistant_detail_alias = aliased(KnowledgeLabelDetail)
        
        # 子查询1：获取每个KnowledgeLabel_id下role='user'的最新版本记录
        user_latest_subq = (
            self.db.query(
                KnowledgeLabelDetail.knowledge_label_id,
                func.max(KnowledgeLabelDetail.version).label('max_version')
            )
            .filter(KnowledgeLabelDetail.role == KnoewledgeRoleEnum.user,
                    KnowledgeLabelDetail.status != KnowledgeStatusEnum.deleted)
            .group_by(KnowledgeLabelDetail.knowledge_label_id)
            .subquery('user_latest')
        )
        
        # 子查询2：获取每个KnowledgeLabel_id下role='assistant'的最新版本记录
        assistant_latest_subq = (
            self.db.query(
                KnowledgeLabelDetail.knowledge_label_id,
                func.max(KnowledgeLabelDetail.version).label('max_version')
            )
            .filter(KnowledgeLabelDetail.role == KnoewledgeRoleEnum.assistant,
                    KnowledgeLabelDetail.status != KnowledgeStatusEnum.deleted)
            .group_by(KnowledgeLabelDetail.knowledge_label_id)
            .subquery('assistant_latest')
        )
        
        # 先获取符合条件的KnowledgeLabel ID列表（用于准确计数）
        base_label_query = self.db.query(KnowledgeLabel.id).filter(
            KnowledgeLabel.status != KnowledgeStatusEnum.deleted
        )
        
        if batch_id:
            base_label_query = base_label_query.filter(KnowledgeLabel.batch_id == batch_id)
        
        if name:
            base_label_query = base_label_query.filter(KnowledgeLabel.name.ilike(f"%{name}%"))
        
        # 准确计算总数 - 只计算KnowledgeLabel的记录数
        total = base_label_query.count()
        
        # 获取分页的KnowledgeLabel ID
        label_ids = []
        if page and size:
            offset = (page - 1) * size
            label_ids = [row[0] for row in base_label_query.order_by(KnowledgeLabel.updated_at.desc()).offset(offset).limit(size).all()]
        else:
            label_ids = [row[0] for row in base_label_query.order_by(KnowledgeLabel.updated_at.desc()).all()]
        
        # 如果没有记录，直接返回空结果
        if not label_ids:
            return PageResponse[KnowledgeLabelWithDetailRead](
                total=total,
                page=page,
                size=size,
                items=[],
                has_next=False,
                has_prev=page > 1
            )
        

        # 主查询：只查询当前页的KnowledgeLabel ID对应的详情
        query = (
            self.db.query(
                KnowledgeLabel.batch_id.label('batch_number'),
                KnowledgeLabel.id.label('label_id'),
                KnowledgeLabel.name.label('question'),
                assistant_detail_alias.content.label('ai_content'),       # AI内容
                user_detail_alias.content.label('user_content'),          # 用户内容   
                user_detail_alias.is_pass.label('is_passed'),             # 是否通过
                user_detail_alias.description.label('description'),       # 原因
                user_detail_alias.filled_by.label('filled_by'),           # 整理人
                KnowledgeLabel.created_at.label('create_time'),           # 时间
                KnowledgeLabel.updated_at.label('update_time'),
            )
            .join(user_detail_alias, and_(
                KnowledgeLabel.id == user_detail_alias.knowledge_label_id,
                user_detail_alias.role == KnoewledgeRoleEnum.user
                ))
            .join(assistant_detail_alias,and_(
                KnowledgeLabel.id == assistant_detail_alias.knowledge_label_id,
                assistant_detail_alias.role == KnoewledgeRoleEnum.assistant))
            .join(user_latest_subq, 
                and_(user_detail_alias.knowledge_label_id == user_latest_subq.c.knowledge_label_id,
                    user_detail_alias.version == user_latest_subq.c.max_version))
            .join(assistant_latest_subq, 
                and_(assistant_detail_alias.knowledge_label_id == assistant_latest_subq.c.knowledge_label_id,
                    assistant_detail_alias.version == assistant_latest_subq.c.max_version))
            .filter(KnowledgeLabel.status != KnowledgeStatusEnum.deleted)
            .filter(KnowledgeLabel.id.in_(label_ids))
            .order_by(KnowledgeLabel.id.desc())
        )

        # if len(filled_by)>0:
        #     query = query.filter(KnowledgeLabel.filled_by.ilike(f"%{filled_by}%"))

        if filled_state == 'passed':
            query = query.filter(user_detail_alias.is_pass == True)
        elif filled_state == 'unchecked':
            query = query.filter(user_detail_alias.is_pass.is_(None))
        elif filled_state == 'unpassed':
            query = query.filter(user_detail_alias.is_pass == False)
        
        # 执行查询
        results = query.all()
        
        # 转换为需要的格式
        items = []
        for row in results:
            item = {
                "batch_number": row.batch_number,
                "label_id": row.label_id,
                "question": row.question,
                "ai_content": row.ai_content,
                "user_content": row.user_content,
                "is_passed": row.is_passed,
                "description": row.description,
                "filled_by": row.filled_by,
                "create_at": row.create_time,
                "update_at": row.update_time
            }
            items.append(item)
        
        # 计算总页数
        total_pages = math.ceil(total / size) if size else 1
        
        return PageResponse[KnowledgeLabelWithDetailRead](
            total=total,
            page=page,
            size=size,
            items=items,
            has_next=page < total_pages,
            has_prev=page > 1
        )