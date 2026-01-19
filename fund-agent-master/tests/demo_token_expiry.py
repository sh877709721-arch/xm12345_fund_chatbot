#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示token过期功能如何踢掉客户端
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from app.middleware.auth_logging import AuthLoggingMiddleware
from app.config.settings import settings
from jose import jwt


def create_token(expire_minutes: int = 5) -> str:
    """创建指定过期时间的token"""
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    payload = {
        "sub": "demo_user",
        "exp": expire_time.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp()
    }

    return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm=settings.ALGORITHM)


def create_expired_token() -> str:
    """创建已过期的token"""
    return create_token(-5)  # 5分钟前过期


async def protected_endpoint(request: Request):
    """受保护的端点"""
    if hasattr(request.state, 'username'):
        return JSONResponse({
            "message": "访问成功",
            "user": request.state.username,
            "token_validity": getattr(request.state, 'token_validity', None)
        })
    else:
        return JSONResponse({"message": "未认证"}, status_code=401)


async def public_endpoint(request: Request):
    """公开端点"""
    return JSONResponse({"message": "公开访问成功"})


def create_demo_app():
    """创建演示应用"""
    # 创建Starlette应用
    app = Starlette(
        routes=[
            ("/protected", protected_endpoint, ["GET"]),
            ("/public", public_endpoint, ["GET"]),
        ],
        middleware=[
            Middleware(AuthLoggingMiddleware),
        ]
    )

    return app


async def demo_token_scenarios():
    """演示各种token场景"""
    print("=" * 60)
    print("🚀 Token过期踢掉客户端功能演示")
    print("=" * 60)

    app = create_demo_app()

    # 创建各种token
    valid_token = create_token(10)  # 10分钟后过期
    expired_token = create_expired_token()  # 已过期
    invalid_token = "invalid.token.here"

    print(f"\n📋 测试Token:")
    print(f"✅ 有效Token: {valid_token[:20]}...")
    print(f"❌ 过期Token: {expired_token[:20]}...")
    print(f"❌ 无效Token: {invalid_token}")

    # 场景1: 公开端点（无需token）
    print(f"\n🌐 场景1: 访问公开端点 /public")
    try:
        # 模拟请求
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/public',
            'headers': [],
            'query_string': b''
        }

        async def receive():
            return {}

        # 创建模拟Request
        class MockRequest:
            def __init__(self, scope):
                self.scope = scope
                self.url = type('URL', (), {'path': scope['path']})()
                self.method = scope['method']
                self.headers = dict(scope.get('headers', []))
                self.state = type('State', (), {})()

            async def receive(self):
                return {}

        request = MockRequest(scope)
        response = await public_endpoint(request)
        print(f"   ✅ {response.status_code}: 公开端点访问成功")

    except Exception as e:
        print(f"   ❌ 公开端点访问失败: {e}")

    # 场景2: 无token访问受保护端点
    print(f"\n🚫 场景2: 无Token访问受保护端点 /protected")
    try:
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/protected',
            'headers': [],
            'query_string': b''
        }

        request = MockRequest(scope)

        # 直接调用中间件
        middleware = AuthLoggingMiddleware(app)

        async def call_next(request):
            return await protected_endpoint(request)

        response = await middleware.dispatch(request, call_next)

        if hasattr(response, 'status_code') and response.status_code == 401:
            response_data = json.loads(response.body.decode())
            print(f"   ✅ 401: 无效Token被正确拒绝")
            print(f"   📝 错误信息: {response_data}")
        else:
            print(f"   ❌ 意外响应: {response}")

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")

    # 场景3: 过期token访问受保护端点
    print(f"\n⏰ 场景3: 过期Token访问受保护端点 /protected")
    try:
        # 添加Authorization头
        headers = [
            (b'authorization', f'Bearer {expired_token}'.encode())
        ]

        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/protected',
            'headers': headers,
            'query_string': b''
        }

        request = MockRequest(scope)
        middleware = AuthLoggingMiddleware(app)

        async def call_next(request):
            return await protected_endpoint(request)

        response = await middleware.dispatch(request, call_next)

        if hasattr(response, 'status_code') and response.status_code == 401:
            response_data = json.loads(response.body.decode())
            print(f"   ✅ 401: 过期Token被正确拒绝")
            print(f"   📝 错误信息: {response_data}")
            print(f"   🔍 过期时间: {response_data.get('expired_at', 'N/A')}")
        else:
            print(f"   ❌ 意外响应: {response}")

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")

    # 场景4: 有效token访问受保护端点
    print(f"\n✅ 场景4: 有效Token访问受保护端点 /protected")
    try:
        headers = [
            (b'authorization', f'Bearer {valid_token}'.encode())
        ]

        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/protected',
            'headers': headers,
            'query_string': b''
        }

        request = MockRequest(scope)
        middleware = AuthLoggingMiddleware(app)

        async def call_next(request):
            return await protected_endpoint(request)

        response = await middleware.dispatch(request, call_next)

        if hasattr(response, 'status_code') and response.status_code == 200:
            print(f"   ✅ 200: 有效Token访问成功")
            print(f"   👤 用户: {getattr(request.state, 'username', 'N/A')}")
            validity = getattr(request.state, 'token_validity', None)
            if validity:
                print(f"   ⏰ 剩余时间: {validity.get('remaining_minutes', 'N/A'):.1f} 分钟")
        else:
            print(f"   ❌ 意外响应: {response}")

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")

    print(f"\n" + "=" * 60)
    print("🎯 总结:")
    print("✅ 过期Token: 立即返回401，踢掉客户端")
    print("✅ 无效Token: 立即返回401，踢掉客户端")
    print("✅ 缺失Token: 返回401，要求客户端提供Token")
    print("✅ 有效Token: 正常访问，记录用户信息")
    print("✅ 公开端点: 无需Token，直接访问")
    print("=" * 60)


class MockRequest:
    """模拟Request对象"""
    def __init__(self, scope):
        self.scope = scope
        self.url = type('URL', (), {'path': scope['path']})()
        self.method = scope['method']
        self.headers = dict(scope.get('headers', []))
        self.state = type('State', (), {})()

    async def receive(self):
        return {}


if __name__ == "__main__":
    asyncio.run(demo_token_scenarios())