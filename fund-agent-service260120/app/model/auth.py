# Copyright (c) 2025 Mingtai Lin.
# Licensed under the MIT License


import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, BIGINT
import datetime
from sqlalchemy import Boolean,ForeignKey,Enum as SQLEnum
from enum import Enum as PyEnum
from pydantic import BaseModel, EmailStr
from app.config.database import Base




class RoleEnum(PyEnum):
    superadmin = "superadmin"
    normal_user = "normal_user"
    engineer = "engineer"


class User(Base):
    __tablename__ = "users"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    user_role = Column(SQLEnum(RoleEnum), default= RoleEnum.normal_user)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


    def set_hashed_password(self, hashed_password: str):
        self.hashed_password = hashed_password
        
    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return True

    def is_active_user(self):
        return self.is_active
    
    def repr(self):
        return f'<User {self.username}>'
    

class UserRoles(Base):
    __tablename__ = "user_roles"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey('users.id'), nullable=False)
    role = Column(SQLEnum(RoleEnum, name="role_enum"), nullable=False)

    