from sqlalchemy import Column, String, DateTime, ForeignKey, Text
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
    vote_id = Column(BIGINT, autoincrement="auto", primary_key=True)
    message_id = Column(BIGINT, ForeignKey("messages.id"))
    vote_type = Column(ENUM(VoteEnum), name='vote_type', nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    #client_type = Column(String, nullable=True)

    def set_vote_type(self, vote_type: VoteEnum):
        self.vote_type = vote_type

    def set_feedback_content(self, feedback_content: str):
        self.feedback = feedback_content
    