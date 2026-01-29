from pydantic import BaseModel, EmailStr
from app.model.auth import RoleEnum

import datetime
# -------------------- Pydantic Schemas --------------------

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class UserReadWithRole(UserBase):
    id: int
    user_role: RoleEnum
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str