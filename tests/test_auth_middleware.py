#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试token过期功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone, timedelta
from jose import jwt
from app.config.settings import settings


def create_expired_token():
    """创建一个已过期的token"""
    # 创建一个5分钟前就过期的token
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    payload = {
        "sub": "test_user",
        "exp": expired_time.timestamp(),
        "iat": (expired_time - timedelta(minutes=10)).timestamp()
    }

    return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm=settings.ALGORITHM)


def create_valid_token():
    """创建一个有效的token"""
    valid_time = datetime.now(timezone.utc) + timedelta(minutes=5)

    payload = {
        "sub": "test_user",
        "exp": valid_time.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp()
    }

    return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm=settings.ALGORITHM)


def test_token_verification():
    """测试token验证功能"""
    from app.middleware.auth_logging import AuthLoggingMiddleware

    middleware = AuthLoggingMiddleware(None)

    print("🔧 测试Token过期功能...")

    # 测试过期token
    print("\n1. 测试过期token:")
    expired_token = create_expired_token()
    print(f"过期token: {expired_token[:20]}...")

    expired_result = middleware._verify_token(expired_token)
    if expired_result:
        validity = middleware._calculate_token_validity(expired_result)
        print(f"✅ 过期token解析成功，有效期: {validity}")
        if validity.get("is_expired"):
            print("✅ 检测到token已过期 - 功能正常")
        else:
            print("❌ 未检测到token过期 - 功能异常")
    else:
        print("❌ 过期token解析失败")

    # 测试有效token
    print("\n2. 测试有效token:")
    valid_token = create_valid_token()
    print(f"有效token: {valid_token[:20]}...")

    valid_result = middleware._verify_token(valid_token)
    if valid_result:
        validity = middleware._calculate_token_validity(valid_result)
        print(f"✅ 有效token解析成功，有效期: {validity}")
        if not validity.get("is_expired"):
            print("✅ 有效token检测正常 - 功能正常")
        else:
            print("❌ 有效token被误判为过期 - 功能异常")
    else:
        print("❌ 有效token解析失败")

    # 测试无效token
    print("\n3. 测试无效token:")
    invalid_token = "invalid_token_12345"
    print(f"无效token: {invalid_token}")

    invalid_result = middleware._verify_token(invalid_token)
    if invalid_result is None:
        print("✅ 无效token被正确拒绝 - 功能正常")
    else:
        print("❌ 无效token未被正确拒绝 - 功能异常")

    print("\n🎉 Token过期功能测试完成!")


def test_auth_path_check():
    """测试认证路径检查功能"""
    from app.middleware.auth_logging import AuthLoggingMiddleware

    middleware = AuthLoggingMiddleware(None)

    print("\n🔧 测试认证路径检查功能...")

    test_paths = [
        ("/v1/admin/users", True, "管理路径"),
        ("/v1/api/chat", True, "API路径"),
        ("/v1/ai/generate", True, "AI路径"),
        ("/v1/auth/token", False, "认证路径"),
        ("/health", False, "健康检查"),
        ("/docs", False, "文档路径"),
        ("/v1/no-match", False, "未匹配路径")
    ]

    for path, expected, description in test_paths:
        result = middleware._requires_auth(path)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {path} -> 需要认证: {result}")


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🚀 开始测试修改后的AuthLoggingMiddleware")
        print("=" * 60)

        test_token_verification()
        test_auth_path_check()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()