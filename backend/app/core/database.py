# 엔진/세션 DI

from __future__ import annotations

from typing import AsyncGenerator
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from backend.app.core.config import settings

# MySQL 연결 URL 생성
def _make_mysql_async_url() -> str:
    # url 인코딩
    user = quote_plus(settings.DB_USER)
    pwd = quote_plus(settings.DB_PASSWORD.get_secret_value())
    host = settings.DB_HOST
    port = settings.DB_PORT
    db = settings.DB_NAME
    # utf8mb4 설정 + SQLAlchemy 2.0 방식 url
    return f"mysql+aiomysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"

# SQLAlchemy 비동기 엔진 생성
engine = create_async_engine(
    _make_mysql_async_url(),
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,  # 커넥션 풀 유효성 검사(커넥션이 끊어졌을 때 재연결)
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    future=True,
)

# 세션 팩토리 (요청 당 1세션)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """"ORM 모델의 Base 클래스"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
        FastAPI 의존성(Dependency) 주입용 세션 생성기.
        요청 당 1세션이 생성되어 반환됨.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise