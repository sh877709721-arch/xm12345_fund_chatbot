
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID,ENUM,TEXT
from app.config.database import Base
from uuid import uuid4
import datetime


class Ticket(Base):
    __tablename__ = "ticket"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content = Column(TEXT)
    user_info = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)
    status = Column(ENUM('open', 'closed'), name='status', nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)