from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum as PyEnum
import logging


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
    priority: Optional[int] = None  # 允许 None，用于处理历史数据
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
    priority: int = Field(default=1, ge=0, le=9999, description="优先级(0-9999, 默认1, 越大优先级越高)")
    status: str = GuidelinesStatusEnum.draft.value

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """验证优先级范围"""
        if v < 0:
            raise ValueError('priority 不能小于 0')
        if v > 9999:
            raise ValueError('priority 不能大于 9999')
        return v


class GuidelinesUpdate(BaseModel):
    """更新指南请求模型"""
    title: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    prompt_template: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=9999, description="优先级(0-9999)")
    status: Optional[str] = None

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[int]) -> Optional[int]:
        """验证优先级范围"""
        if v is not None and (v < 0 or v > 9999):
            raise ValueError('priority 必须在 0-9999 之间')
        return v


class GuidelinesSearchRequest(BaseModel):
    """指南搜索请求模型"""
    title: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    priority_min: Optional[int] = Field(default=None, ge=0, description="最小优先级")
    priority_max: Optional[int] = Field(default=None, le=9999, description="最大优先级")
    orderby: Optional[str] = Field(default="priority", description="排序字段: id/priority/created_time/updated_time")
    order: Optional[str] = Field(default="desc", description="排序方向: asc/desc")
    page: int = 1
    size: int = 10

    @field_validator('orderby')
    @classmethod
    def validate_orderby(cls, v: str) -> str:
        """验证排序字段"""
        allowed = {'id', 'priority', 'created_time', 'updated_time'}
        if v not in allowed:
            raise ValueError(f'orderby 必须是 {allowed} 之一')
        return v

    @field_validator('order')
    @classmethod
    def validate_order(cls, v: str) -> str:
        """验证排序方向"""
        if v.lower() not in {'asc', 'desc'}:
            raise ValueError('order 必须是 asc 或 desc')
        return v.lower()


class GuidelinesMatchRequest(BaseModel):
    """指南匹配请求模型"""
    context: str = Field(..., min_length=1, description="对话上下文或用户查询")
    candidate_top_k: int = Field(default=5, ge=1, le=10, description="返回给 LLM 精选的候选数量")
    vector_top_k: int = Field(default=20, ge=1, le=100, description="向量检索返回的候选数量")
    bm25_top_k: int = Field(default=20, ge=1, le=100, description="BM25 检索返回的候选数量")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="向量相似度阈值")
    use_llm_refinement: bool = Field(default=True, description="是否使用 LLM 精选")


class GuidelinesMatchResult(BaseModel):
    """指南匹配结果模型"""
    guideline_id: int
    title: str
    condition: str
    action: str
    prompt_template: Optional[str] = None
    priority: Optional[int] = None
    match_score: float = Field(..., ge=0.0, le=1.0, description="匹配分数")
    match_method: str = Field(..., description="匹配方法：vector/bm25/rrf/llm")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")

    class Config:
        from_attributes = True
