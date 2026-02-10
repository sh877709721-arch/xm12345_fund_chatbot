from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.model.vote import VoteEnum


class VoteCreate(BaseModel):
    """创建投票请求模型"""
    message_id: int
    vote_type: VoteEnum
    feedback: Optional[str] = None


class VoteRead(BaseModel):
    """投票响应模型"""
    vote_id: int
    message_id: int
    vote_type: VoteEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VoteUpdate(BaseModel):
    """更新投票请求模型"""
    vote_type: VoteEnum


class VoteStats(BaseModel):
    """投票统计模型"""
    message_id: int
    good_count: int
    average_count: int
    poor_count: int
    total_count: int


class VoteWithMessage(BaseModel):
    """带问题答案的投票响应模型"""
    vote_id: Optional[int]
    message_id: int
    vote_type: Optional[VoteEnum]
    feedback: Optional[str] = None
    question: Optional[str] = None  # 用户问题
    answer: Optional[str] = None   # AI回答
    chat_id: UUID
    created_at: Optional[datetime]
    client_type: Optional[str]
    

    class Config:
        from_attributes = True