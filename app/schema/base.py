# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License


from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from fastapi.responses import Response
# 定义泛型
T = TypeVar('T')

# 基础响应模型
class BaseResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T

# 分页响应模型
class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool