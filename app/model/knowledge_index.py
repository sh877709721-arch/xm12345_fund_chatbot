from sqlalchemy import Column, String, DateTime,Text
from sqlalchemy.dialects.postgresql import BIGINT
from app.config.database import Base

import datetime


# 知识标注
class IndexedKnowledge(Base):
    __tablename__ = "indexed_knowledge"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    knowledge_id = Column(BIGINT)
    title = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    reference = Column(Text, nullable=True)
    status = Column(String(255), nullable=False,default='A')
    created_time = Column(DateTime, default=datetime.datetime.now)
    updated_time = Column(DateTime, default=datetime.datetime.now, onupdate= datetime.datetime.now)



    def set_status(self, status):
        self.status = status

    def repr(self):
        return f'<KnowledgeLabelBatch {self.name}>'