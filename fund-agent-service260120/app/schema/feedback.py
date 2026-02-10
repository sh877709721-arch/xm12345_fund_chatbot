from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ImageInfo(BaseModel):
    """图片信息模型"""
    url: str  # 图片访问URL
    filename: str  # 原始文件名
    size: int  # 文件大小（字节）
    content_type: str  # 文件MIME类型
    path: str  # 服务器存储路径


class FeedbackCreate(BaseModel):
    """创建反馈的请求模型"""
    content: str
    phone: Optional[str] = None
    images: Optional[List[ImageInfo]] = None


class FeedbackUpdate(BaseModel):
    """更新反馈的请求模型"""
    content: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    images: Optional[List[ImageInfo]] = None


class FeedbackRead(BaseModel):
    """反馈响应模型"""
    id: int
    content: str
    phone: Optional[str]
    status: str
    images: Optional[List[ImageInfo]] = None
    created_time: datetime
    updated_time: datetime

    class Config:
        from_attributes = True


class ImageUploadResponse(BaseModel):
    """图片上传响应模型"""
    url: str
    filename: str
    size: int
    content_type: str
    path: str