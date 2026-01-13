# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License


# -------------------- Imports --------------------
from fastapi import APIRouter, Depends, HTTPException, status, Request,Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.model.auth import User
from app.config.database import get_db
from app.service.auth import AuthService
from app.schema.auth import Token, ResetPasswordRequest, UserCreate, UserReadWithRole
from app.schema.base import BaseResponse
from app.middleware.api_rate_limiter import limiter, get_rate_limit_key_by_ip

router = APIRouter(prefix="/auth")



# 创建 AuthService 实例
auth_service = AuthService()

# -------------------- Routes --------------------
@router.post("/register", response_model=BaseResponse[UserReadWithRole])
def register(user: UserCreate, db: Session = Depends(get_db)):
    user = auth_service.register_user(user, db)
    return BaseResponse(data=UserReadWithRole.model_validate(user))

@router.post("/token", response_model=Token) #BaseResponse[Token]
@limiter.limit("5/minute", key_func=get_rate_limit_key_by_ip)
def login_for_access_token(request: Request, response: Response,
                           form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录认证接口

    限流规则：5次/分钟（按 IP）
    - 防止暴力破解
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer") #BaseResponse[Token](data=Token(access_token=access_token, token_type="bearer"))

@router.get("/me", response_model=BaseResponse[UserReadWithRole]) #
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    获取当前用户信息
    """
    return BaseResponse[UserReadWithRole](data=current_user)

@router.post("/reset-password", response_model=BaseResponse[dict])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    #user = auth_service.get_user_by_username(db, req.username)
    #if not user:
    #    raise HTTPException(status_code=404, detail="User not found")
    #user.hashed_password = auth_service.get_password_hash(req.new_password)
    #db.commit()
    return BaseResponse[dict](data={"msg": "Password reset successful"})



# 前端
@router.post("/front_token",response_model=BaseResponse[Token]) # 
@limiter.limit("5/minute", key_func=get_rate_limit_key_by_ip)
def front_login_for_access_token(request: Request, response: Response,
                                 form_data: OAuth2PasswordRequestForm = Depends(), 
                                 db: Session = Depends(get_db)):
    """
    前端用户登录认证接口

    限流规则：5次/分钟（按 IP）
    - 防止暴力破解
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return BaseResponse[Token](data=Token(access_token=access_token, token_type="bearer"))
