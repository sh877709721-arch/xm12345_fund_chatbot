# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License

"""
API 请求级别限流中间件

基于 slowapi 实现，支持：
- 用户优先限流策略（用户名 > IP地址）
- 登录接口强制按IP限流
- 不同接口差异化限流
- 自定义限流键函数
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.schema.base import BaseResponse
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 核心函数：智能限流键生成
# ============================================================================

def get_rate_limit_key(request: Request) -> str:
    """
    智能获取限流标识符

    优先级策略：
    1. 认证用户：使用 request.state.username（来自 JWT token）
    2. 匿名用户：降级到 IP 地址

    Args:
        request: FastAPI 请求对象

    Returns:
        str: 限流标识符
    """
    # 1. 尝试从认证中间件获取用户名
    if hasattr(request.state, 'username') and request.state.username:
        username = request.state.username
        logger.debug(f"限流键来源: 用户名 {username}")
        return f"user:{username}"

    # 2. 降级到 IP 地址
    ip_address = _get_client_ip(request)
    logger.debug(f"限流键来源: IP {ip_address}")
    return f"ip:{ip_address}"


def get_rate_limit_key_by_ip(request: Request) -> str:
    """
    强制按 IP 限流（用于登录接口）

    登录场景：
    - 用户尚未认证，没有 username
    - 需要防止暴力破解，按 IP 限流更安全

    Args:
        request: FastAPI 请求对象

    Returns:
        str: IP 限流标识符
    """
    ip_address = _get_client_ip(request)
    logger.debug(f"登录接口限流键来源: IP {ip_address}")
    return f"ip:{ip_address}"


def _get_client_ip(request: Request) -> str:
    """
    获取客户端真实 IP 地址

    优先级：
    1. X-Forwarded-For（代理头部，取第一个IP）
    2. X-Real-IP（真实IP）
    3. request.client.host（直连IP）

    Args:
        request: FastAPI 请求对象

    Returns:
        str: IP 地址
    """
    # 1. 从代理头部获取真实IP（考虑多级代理）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个IP（客户端真实IP）
        return forwarded_for.split(",")[0].strip()

    # 2. 尝试 X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 3. 获取直连IP
    if hasattr(request, 'client') and request.client:
        return request.client.host

    # 4. 兜底返回
    return "127.0.0.1"


# ============================================================================
# 创建 Limiter 实例
# ============================================================================

# 创建全局限流器实例
# 使用自定义的 key_func 实现用户/IP混合限流
limiter = Limiter(
    key_func=get_rate_limit_key,
    headers_enabled=True,  # 启用响应头中的限流信息
    storage_uri="memory://",  # 使用内存存储（可升级到 Redis）
)


# ============================================================================
# 自定义异常处理器
# ============================================================================

def custom_rate_limit_handler(request: Request, exc: Exception):
    """
    自定义限流异常处理器

    返回友好的中文错误信息
    """
    # 确保是 RateLimitExceeded 异常
    if not isinstance(exc, RateLimitExceeded):
        raise exc

    # 获取限流标识符
    identifier = _get_identifier_friendly_name(request)

    # 构建友好的错误响应
    error_detail = {
        "error": "请求过于频繁",
        "message": "您已超过请求频率限制，请稍后再试",
        "code": "RATE_LIMIT_EXCEEDED",
        "identifier": identifier
    }

    logger.warning(
        f"限流触发 | 标识符: {identifier} | "
        f"路径: {request.url.path}"
    )

    return JSONResponse(
       status_code=429,
       content=error_detail
    )


def _get_identifier_friendly_name(request: Request) -> str:
    """获取友好的标识符名称（用于错误提示）"""
    if hasattr(request.state, 'username') and request.state.username:
        return request.state.username
    return _get_client_ip(request)


# ============================================================================
# 导出接口
# ============================================================================

__all__ = [
    "limiter",
    "get_rate_limit_key",
    "get_rate_limit_key_by_ip",
    "custom_rate_limit_handler",
]
