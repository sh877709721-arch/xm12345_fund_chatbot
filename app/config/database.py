from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy.pool import QueuePool
from app.config.settings import settings

from pgvector.psycopg2 import register_vector
import psycopg2
from contextlib import contextmanager
import logging


# SQLAlchemy engine for PostgreSQL - 🔧 **优化后的连接池配置**
engine = create_engine(
    settings.CHAT_POSTGRES_URL,
    # 🔧 **连接池优化：支持更高并发，减少连接等待**
    # 基于流式响应优化的连接池配置
    pool_size=20,  # 增加基础连接数，支持更多并发请求
    # 最大溢出连接数：允许在pool_size基础上的额外连接
    max_overflow=10,  # 增加溢出连接数，处理突发流量
    # 连接超时时间：减少等待时间，快速响应
    pool_timeout=30,  # 减少到30秒，避免长时间等待
    # 连接回收时间：连接在池中闲置多久后被回收（秒）
    pool_recycle=300,  # 减少到10分钟，更频繁地回收连接，避免连接老化
    # 预ping检查：确保连接在checkout时是有效的
    pool_pre_ping=True,
    # 连接池事件记录
    echo=False,
    # 连接池类：使用QueuePool确保连接的线程安全
    poolclass=QueuePool,
    # 🔧 **新增配置：优化连接回收策略**
    pool_reset_on_return='commit',  # 连接返回时自动commit，避免事务状态问题
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(
    settings.ASYNC_CHAT_POSTGRES_URL,
    # 🔧 **异步引擎连接池优化配置**
    pool_size=15,  # 与同步引擎保持一致
    max_overflow=15,  # 增加溢出连接数
    pool_timeout=30,  # 减少等待时间
    pool_recycle=300,  # 减少到10分钟，保持连接新鲜度
    pool_pre_ping=True,
    echo=False,
    # 异步引擎特有的连接返回策略
    pool_reset_on_return='commit',
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False
)

# FastAPI依赖注入数据库Session
def get_db():
    db = SessionLocal()
    try:
        # 🔧 **性能监控：记录连接创建时间**
        import time
        start_time = time.time()
        logging.debug(f"Database connection created at {start_time}")
        yield db
        # 🔧 **性能监控：记录连接使用时长**
        usage_time = time.time() - start_time
        logging.debug(f"Database connection used for {usage_time:.3f}s")
    finally:
        db.close()
        logging.debug("Database connection closed")

async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db


@contextmanager
def get_sqlalchemy_engine():
    """支持pgvector的SQLAlchemy引擎"""
    engine = create_engine(settings.CHAT_POSTGRES_URL)

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        register_vector(dbapi_connection)
        if isinstance(dbapi_connection, psycopg2.extensions.connection):
            register_vector(dbapi_connection)
    
    try:
        yield engine
    finally:
        pass
        #engine.dispose()

global_schema = "housing_fund" # TODO: 注意要修改这里 chatbot

Base = declarative_base(metadata=MetaData(schema=global_schema)) 



