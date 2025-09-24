"""
트랜잭션 헬퍼
"""
import aiomysql
from typing import AsyncGenerator, Any, Dict
from contextlib import asynccontextmanager
from .pool import get_pool

@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiomysql.Connection, None]:
    """데이터베이스 연결 획득"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn

@asynccontextmanager
async def get_cursor() -> AsyncGenerator[aiomysql.Cursor, None]:
    """커서 획득 (자동 커밋)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                yield cursor
                await conn.commit()  # 자동 커밋
        except Exception:
            await conn.rollback()  # 오류 시 롤백
            raise

@asynccontextmanager
async def transaction() -> AsyncGenerator[aiomysql.Connection, None]:
    """트랜잭션 컨텍스트"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.begin()
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
