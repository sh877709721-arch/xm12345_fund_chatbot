
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID,ENUM
from enum import Enum as PyEnum
from app.config.database import Base
from uuid import uuid4
import datetime

class ChatStatusEnum(PyEnum):
    active = 'active'
    deleted = 'deleted'

class Chat(Base):
    __tablename__ = "chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=True)
    status = Column(ENUM(ChatStatusEnum), name='status', nullable=False)
    user_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    