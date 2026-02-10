from sqlalchemy import Column, String, DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import TEXT,ENUM,BIGINT, BOOLEAN
from app.config.database import Base
from app.model.knowledge import KnowledgeStatusEnum,KnoewledgeRoleEnum
from uuid import uuid4
import datetime


# 知识标注
class KnowledgeLabelBatch(Base):
    __tablename__ = "knowledge_label_batch"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False,default=KnowledgeStatusEnum.active)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now)

    def set_name(self, name):
        self.name = name

    def set_status(self, status):
        self.status = status

    def repr(self):
        return f'<KnowledgeLabelBatch {self.name}>'



# 知识: 问题 
class KnowledgeLabel(Base):
    __tablename__ = "knowledge_label"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    batch_id = Column(BIGINT, ForeignKey("knowledge_label_batch.id"))
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False)
    created_by = Column(BIGINT, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def set_state(self, status):
        self.status = status

    def set_name(self, name):
        self.name = name

    

# 知识标注: 答案
class KnowledgeLabelDetail(Base):
    __tablename__ = "knowledge_label_detail"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    knowledge_label_id = Column(BIGINT, ForeignKey("knowledge_label.id"))
    content = Column(TEXT, nullable=True)
    context = Column(TEXT, nullable=True)
    role = Column(ENUM(KnoewledgeRoleEnum), nullable=True)
    is_pass = Column(BOOLEAN, nullable=True)
    version = Column(BIGINT, nullable=True)
    description = Column(TEXT, nullable=True)
    filled_by = Column(String(255), nullable=True)
    created_by = Column(BIGINT, nullable=True)
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def set_state(self, status):
        self.status = status

