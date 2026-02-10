from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TEXT, ENUM, BIGINT, JSONB, TSVECTOR
from enum import Enum as PyEnum
from app.config.database import Base
from uuid import uuid4
import datetime

class KnowledgeStatusEnum(PyEnum):
    active = 'active'
    pending = 'pending'
    indexing = 'indexing'
    idle = 'idle'
    deleted = 'deleted'

# 知识类型
class KnowledgeTypeEnum(PyEnum):
    document = 'document'
    data_table = 'data_table'
    qa = 'qa'

# 填表角色
class KnoewledgeRoleEnum(PyEnum):
    system = 'system'
    user = 'user'
    assistant = 'assistant'
    admin = 'admin'
    assistant_admin = 'assistant_admin'
    

# 知识目录
class KnowledgeCatalog(Base):
    __tablename__ = "knowledge_catalog"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    category_level_1 = Column(String(255), nullable=True)
    category_level_2 = Column(String(255), nullable=True)
    category_level_3 = Column(String(255), nullable=True) 
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

# 知识表格
class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    knowledge_type = Column(ENUM(KnowledgeTypeEnum), name='knowledge_type', nullable=False)
    knowledge_catalog_id = Column(BIGINT, ForeignKey("knowledge_catalog.id"))
    name = Column(String(255), nullable=True)
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False)
    created_by = Column(BIGINT, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


# 知识详情
class KnowledgeDetail(Base):
    __tablename__ = "knowledge_detail"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    knowledge_id = Column(BIGINT, ForeignKey("knowledge.id"))
    content = Column(TEXT, nullable=True)
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False)
    role = Column(String(255), nullable=True)
    reference = Column(TEXT, nullable=True)
    version = Column(BIGINT, nullable=True)
    filled_by = Column(String(255), nullable=True)
    created_by = Column(BIGINT, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)



class KnowledgeData(Base):
    __tablename__ = "knowledge_data"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    knowledge_id = Column(BIGINT, ForeignKey("knowledge.id"))
    content = Column(JSONB, nullable=True)
    fts_content = Column(TSVECTOR, nullable=True)
    status = Column(ENUM(KnowledgeStatusEnum), name='status', nullable=False)
    created_by = Column(BIGINT, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    __table_args__ = (
        Index('idx_chatbot_knowledge_data_knowledge_id', 'knowledge_id'),
        Index('idx_chatbot_indexed_knowledge_fts', 'fts_content', postgresql_using='gin'),
    )
