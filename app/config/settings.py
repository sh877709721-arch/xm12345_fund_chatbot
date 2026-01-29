from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

class Settings(BaseSettings):
    """
    应用配置类，用于管理环境变量和配置项
    """

    BASE_URL: str = ''
    API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None  # 注意：你原文写的是 OPENAP_BASE_KEY，疑似笔误
    OPENAI_MODEL: Optional[str] = None 

    EMBEDDING_MODEL: Optional[str] = 'bge-m3'
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_API_KEY: Optional[str] = None

    #ETL_POSTGRES_URL: str = ''
    CHAT_POSTGRES_URL: str = ''
    ASYNC_CHAT_POSTGRES_URL: str = ''
    #ASYNC_ETL_POSTGRES_URL: str = ''
    

    # 用户认证配置
    NEXTAUTH_SECRET: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # 讯飞语音识别配置
    SPEECH_APP_ID: str = ''
    SPEECH_API_SECRET: str = ''
    SPEECH_API_KEY: str = ''


    # 使用 model_config + SettingsConfigDict 替代 class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

# 使用配置
settings = Settings()


# 用户密码
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/znkfzs/v1/auth/token")