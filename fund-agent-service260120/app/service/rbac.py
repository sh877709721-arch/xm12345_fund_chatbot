# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License

"""
RBAC 权限控制服务
提供基于角色的访问控制依赖函数
"""

from fastapi import Depends, HTTPException, status
from typing import List
from app.service.auth import get_current_user
from app.schema.auth import UserReadWithRole
from app.model.auth import RoleEnum


# -------------------- 权限检查依赖函数 -------------------- #

def require_admin(
    current_user: UserReadWithRole = Depends(get_current_user)
) -> UserReadWithRole:
    """
    要求管理员角色（superadmin 或 engineer）才能访问

    Example:
        @router.get("/admin-only")
        async def admin_route(
            _: UserReadWithRole = Depends(require_admin)
        ):
            return {"message": "Admin access granted"}
    """
    if current_user.user_role not in [RoleEnum.superadmin, RoleEnum.engineer]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足。当前角色：{current_user.user_role.value}",
        )
    return current_user


def require_any_role(
    current_user: UserReadWithRole = Depends(get_current_user)
) -> UserReadWithRole:
    """
    要求任意认证用户（所有角色）

    用于确保用户已登录，但不限制角色

    Example:
        @router.get("/authenticated")
        async def authenticated_route(
            current_user: UserReadWithRole = Depends(require_any_role)
        ):
            return {"message": f"Hello {current_user.username}"}
    """
    return current_user
