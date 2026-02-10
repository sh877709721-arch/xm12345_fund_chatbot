from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID,ENUM,BIGINT

import datetime
from app.config.database import Base
from enum import Enum as PyEnum
from .chat import Chat
from .message import Message

class ContextType(PyEnum):
    thought = "thought"
    observation = "observation"
    action = "action"
    summary = "summary"  #历史对话的总结
    question = "question" #你可能想问
    

class ChatContext(Base):
    __tablename__ = "message_context"
    id = Column(BIGINT, primary_key=True, autoincrement=True) #
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"))
    message_id = Column(BIGINT, ForeignKey("messages.id"))
    context = Column(Text, nullable=True)
    context_type = Column(ENUM(ContextType), name='context_type', nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)





from pydantic import BaseModel
from typing import Optional
import uuid

class ChatContextRead(BaseModel):
    id: int
    chat_id: uuid.UUID
    context: str
    context_type: Optional[ContextType]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        from_attributes = True