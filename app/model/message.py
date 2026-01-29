from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID,ENUM,JSONB,BIGINT

import datetime
import uuid
from app.config.database import Base
from enum import Enum as PyEnum
from uuid import uuid4
from .chat import Chat

class MessageRoleEnum(PyEnum):
    system = "system"
    user = "user"
    assistant = "assistant"

class Message(Base):
    __tablename__ = "messages"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"))
    role =  Column(ENUM(MessageRoleEnum), name='message_role_enum', nullable=False)
    content = Column(Text, nullable=True)
    metadata_ = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def set_content(self, content):
        self.updated_at = datetime.datetime.now()
        self.content = content
        



from pydantic import BaseModel
from typing import Optional

class MessageRead(BaseModel):
    id: int
    chat_id: uuid.UUID
    role: str
    content: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        from_attributes = True