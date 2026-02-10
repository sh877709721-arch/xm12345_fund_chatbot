from sqlalchemy import Column, String, DateTime, Text, Index, func
from sqlalchemy.dialects.postgresql import BIGINT
from app.config.database import Base
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql import operators

import datetime


class Vector(UserDefinedType):
    def __init__(self, dimensions=None):
        self.dimensions = dimensions
    
    def get_col_spec(self, **kw):
        if self.dimensions is not None:
            return f"vector({self.dimensions})"
        return "vector"

# 知识标注
class Guidelines(Base):
    __tablename__ = "guidelines"
    id = Column(BIGINT, primary_key=True, autoincrement=True)    
    title = Column(String(512), nullable=False)
    condition = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    prompt_template = Column(Text, nullable=True)
    condition_embedding = Column(Vector(1024))
    condition_fts = Column(TSVECTOR)
    priority = Column(
        BIGINT,
        nullable=False,
        server_default='1',  # 数据库默认值
        default=1  # Python 默认值
    )
    status = Column(String(255), nullable=False,default='A')
    created_time = Column(DateTime, default=datetime.datetime.now)
    updated_time = Column(DateTime, default=datetime.datetime.now, onupdate= datetime.datetime.now)




     # 索引
    __table_args__ = (
        Index('idx_condition_fts', 'condition_fts', postgresql_using='gin'),
    )

    def set_status(self, status):
        self.status = status

    def set_condition_embedding(self, embedding):
        self.condition_embedding = embedding

    def set_condition_fts(self):
        self.condition_fts = func.setweight(
                func.to_tsvector('zhparsercfg', self.condition), 'A'
            )

    def repr(self):
        return f'<Guidelines {self.name}>'

