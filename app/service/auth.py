# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License

"""
Auth 服务模块
负责用户认证、密码校验、Token生成与校验、当前用户依赖等功能。
依赖 FastAPI、SQLAlchemy、python-jose、passlib。
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.config.database import get_db
from app.model.auth import User, UserRoles, RoleEnum
from app.schema.auth import UserCreate, UserReadWithRole
from app.config.settings import settings, pwd_context, oauth2_scheme
import uuid


NEXTAUTH_SECRET = settings.NEXTAUTH_SECRET
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    """
    认证服务类，封装所有与用户认证相关的功能
    """

    def __init__(self):
        self.secret_key = NEXTAUTH_SECRET
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

    # -------------------- Utility Functions --------------------
    def verify_password(self, plain_password, hashed_password):
        """
        验证明文密码与哈希密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        """
        对密码进行哈希处理
        """
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        """
        创建访问令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def get_user_by_username(self, db: Session, username: str):
        """
        根据用户名获取用户
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, db: Session, email: str):
        """
        根据邮箱获取用户
        """
        return db.query(User).filter(User.email == email).first()

    def authenticate_user(self, db: Session, username: str, password: str):
        """
        验证用户身份
        """
        #user = self.get_user_by_username(db, username)
        user = self.get_user_by_email(db, email=username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    # -------------------- User Service --------------------
    def register_user(self, user_create: UserCreate, db: Session):
        """
        注册新用户
        """
        db_user = db.query(User).filter(User.username == user_create.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        db_email = db.query(User).filter(User.email == user_create.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = self.get_password_hash(user_create.password)
        new_user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        # 分配 normal_user 角色
        user_role = UserRoles(user_id=new_user.id, role=RoleEnum.normal_user)
        db.add(user_role)
        db.commit()
        return new_user

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserReadWithRole:
        """
        获取当前用户依赖项
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        username = None
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = self.get_user_by_username(db, username)
        if user is None:
            raise credentials_exception
        return UserReadWithRole.model_validate(user)
   
    
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserReadWithRole:
    """
    获取当前用户依赖项
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = None
    try:
        payload = jwt.decode(token, settings.NEXTAUTH_SECRET, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return UserReadWithRole.model_validate(user)
    