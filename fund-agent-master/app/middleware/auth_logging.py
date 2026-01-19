# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License

"""
用户认证中间件
简单功能：拦截请求、解析JWT token、记录用户信息和有效期
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from jose import JWTError, jwt, ExpiredSignatureError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config.settings import settings


# 配置简单日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth.middleware")

security = HTTPBearer(auto_error=False)


class AuthLoggingMiddleware(BaseHTTPMiddleware):
    """
    简单的用户认证中间件
    功能：
    1. 解析Authorization header中的JWT token
    2. 计算token有效期
    3. 记录用户信息到请求状态
    4. 简单的认证日志记录
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/debug-now",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/assets/",
            "/workspace/",
            "/v1/auth/token",
            "/v1/auth/front_token",
            "/v1/chat/get_reference_content"
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # 检查是否在排除路径中
        if self._should_exclude_path(request.url.path):
            return await call_next(request)

        # 尝试从请求头获取token
        credentials: Optional[HTTPAuthorizationCredentials] = await security(request)

        if credentials:
            token_info = self._verify_token(credentials.credentials)
            if token_info:
                # 计算有效期
                validity = self._calculate_token_validity(token_info)

                # 检查token是否过期，如果过期直接返回401
                if validity.get("is_expired", False):
                    self._log_token_expired(request, token_info)
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Token已过期，请重新登录",
                            "code": "TOKEN_EXPIRED",
                            "expired_at": validity.get("expires_at"),
                            "current_time": validity.get("current_time")
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # 将token信息添加到请求状态中
                request.state.token_info = token_info
                request.state.username = token_info.get("sub")
                request.state.token_validity = validity

                # 记录简单的认证日志
                self._log_auth_success(request, token_info, validity)
            else:
                self._log_auth_failure(request, "Token无效")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Token验证失败",
                        "code": "INVALID_TOKEN"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
        else:
            self._log_no_token(request)
            # 对于需要认证的路径，直接返回401
            if self._requires_auth(request.url.path):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "需要认证Token",
                        "code": "MISSING_TOKEN"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )

        # 处理请求
        response = await call_next(request)

        # 添加用户信息到响应头
        if hasattr(request.state, 'username'):
            response.headers["X-User-Name"] = request.state.username
        if hasattr(request.state, 'token_validity'):
            response.headers["X-Token-Expires-In"] = str(
                request.state.token_validity.get('expires_in_hours', 0)
            )

        return response

    def _should_exclude_path(self, path: str) -> bool:
        """检查路径是否应该排除认证"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.NEXTAUTH_SECRET,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except ExpiredSignatureError as e:
            # Token过期但格式正确，返回payload以便上层处理
            logger.warning(f"JWT token已过期: {str(e)}")
            try:
                # 不验证过期时间，仅解析payload
                payload = jwt.decode(
                    token,
                    settings.NEXTAUTH_SECRET,
                    algorithms=[settings.ALGORITHM],
                    options={"verify_exp": False}
                )
                return payload
            except Exception:
                return None
        except JWTError as e:
            logger.warning(f"JWT token验证失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token验证异常: {str(e)}")
            return None

    def _calculate_token_validity(self, token_info: Dict[str, Any]) -> Dict[str, Any]:
        """计算token有效期信息"""
        try:
            exp_timestamp = token_info.get("exp")
            current_timestamp = datetime.now(timezone.utc).timestamp()

            if not exp_timestamp:
                return {"error": "Token没有过期时间"}

            exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc)
            current_datetime = datetime.now(timezone.utc)

            # 计算剩余时间
            time_remaining = exp_datetime - current_datetime
            expires_in_hours = time_remaining.total_seconds() / 3600
            is_expired = time_remaining.total_seconds() <= 0

            return {
                "expires_at": exp_datetime.isoformat(),
                "current_time": current_datetime.isoformat(),
                "expires_in_hours": expires_in_hours,
                "is_expired": is_expired,
                "remaining_minutes": time_remaining.total_seconds() / 60
            }
        except Exception as e:
            return {"error": f"计算有效期失败: {str(e)}"}

    def _log_auth_success(self, request: Request, token_info: Dict[str, Any], validity: Dict[str, Any]):
        """记录认证成功日志"""
        username = token_info.get("sub", "未知用户")
        expires_in = validity.get('expires_in_hours', 0)

        logger.info(f"✅ 用户 {username} 认证成功 | "
                   f"路径: {request.url.path} | "
                   f"Token剩余: {expires_in:.1f}小时 | "
                   f"IP: {self._get_client_ip(request)}")

    def _log_auth_failure(self, request: Request, reason: str):
        """记录认证失败日志"""
        logger.warning(f"❌ 认证失败: {reason} | "
                      f"路径: {request.url.path} | "
                      f"IP: {self._get_client_ip(request)}")

    def _log_token_expired(self, request: Request, token_info: Dict[str, Any]):
        """记录Token过期日志"""
        username = token_info.get("sub", "未知用户")
        logger.warning(f"🚫 Token已过期 | 用户: {username} | "
                      f"路径: {request.url.path} | "
                      f"IP: {self._get_client_ip(request)} | "
                      f"需要重新登录")

    def _requires_auth(self, path: str) -> bool:
        """检查路径是否需要认证"""
        auth_required_patterns = [
            "/v1/admin",
            "/v1/api",
            "/v1/ai",
            "/v1/chat",
            "/v1/user"
        ]
        return any(path.startswith(pattern) for pattern in auth_required_patterns)

    def _log_no_token(self, request: Request):
        """记录无token日志（仅对需要认证的路径）"""
        # 对于需要认证但没token的路径，记录警告
        if self._requires_auth(request.url.path):
            logger.warning(f"⚠️ 需要认证的请求缺少Token: {request.method} {request.url.path}")

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 尝试从代理头部获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 获取直连IP
        if hasattr(request, 'client') and request.client:
            return request.client.host

        return "Unknown"


# 辅助函数：获取当前请求中的用户信息
def get_current_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """从请求中获取当前用户信息"""
    if hasattr(request.state, 'token_info'):
        return {
            "username": request.state.username,
            "token_info": getattr(request.state, 'token_info', None),
            "token_validity": getattr(request.state, 'token_validity', None)
        }
    return None


def get_token_info_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """从请求中获取token信息"""
    if hasattr(request.state, 'token_info'):
        return request.state.token_info
    return None


def get_username_from_request(request: Request) -> Optional[str]:
    """从请求中获取用户名"""
    return getattr(request.state, 'username', None)


def get_token_validity_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """从请求中获取token有效期信息"""
    return getattr(request.state, 'token_validity', None)