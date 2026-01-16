from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Identity
from sqlalchemy.dialects.postgresql import ENUM,BIGINT

from datetime import datetime
from app.config.database import Base
from enum import Enum as PyEnum
from .message import Message

class VoteEnum(PyEnum):
    good = "good"
    medium = "medium"
    bad = "bad"
    unknown = "unknown"


class Vote(Base):
    __tablename__ = "vote"
    vote_id = Column(BIGINT, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False), primary_key=True)
    message_id = Column(BIGINT, ForeignKey("messages.id"))
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    vote_type = Column(ENUM(VoteEnum), name='vote_type', nullable=False)
    #client_type = Column(String, nullable=True)
    