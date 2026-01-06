from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum as PyEnum


class GuidelinesStatusEnum(PyEnum):
    """指南状态枚举"""
    active = 'A'      # 激活状态
    inactive = 'I'    # 未激活
    draft = 'D'       # 草稿
    deleted = 'X'     # 已删除


class GuidelinesRead(BaseModel):
    """指南响应模型"""
    id: int
    title: str
    condition: str
    action: str
    prompt_template: Optional[str] = None
    status: str
    created_time: datetime
    updated_time: datetime

    class Config:
        from_attributes = True


class GuidelinesCreate(BaseModel):
    """创建指南请求模型"""
    title: str
    condition: str
    action: str
    prompt_template: Optional[str] = None
    status: str = GuidelinesStatusEnum.draft.value


class GuidelinesUpdate(BaseModel):
    """更新指南请求模型"""
    title: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    prompt_template: Optional[str] = None
    status: Optional[str] = None


class GuidelinesSearchRequest(BaseModel):
    """指南搜索请求模型"""
    title: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    size: int = 10
