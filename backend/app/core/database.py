# aiomysql 연결 관리

from __future__ import annotations

from typing import AsyncGenerator, Dict, Any, List, Optional
import aiomysql
import asyncio
from contextlib import asynccontextmanager

from core.config import settings

# MySQL 연결 설정
def _get_mysql_config() -> Dict[str, Any]:
    """MySQL 연결 설정 반환"""
    return {
        'host': settings.DB_HOST,
        'port': settings.DB_PORT,
        'user': settings.DB_USER,
        'password': settings.DB_PASSWORD.get_secret_value(),
        'db': settings.DB_NAME,
        'charset': 'utf8mb4',
        'autocommit': False,
        'minsize': 1,
        'maxsize': settings.DB_POOL_SIZE,
    }

# aiomysql 연결 풀 관리
_pool: Optional[aiomysql.Pool] = None

async def init_db_pool():
    """데이터베이스 연결 풀 초기화"""
    global _pool
    if _pool is None:
        config = _get_mysql_config()
        _pool = await aiomysql.create_pool(**config)
    return _pool

async def close_db_pool():
    """데이터베이스 연결 풀 종료"""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None

@asynccontextmanager
async def get_db_connection():
    """데이터베이스 연결 컨텍스트 매니저"""
    if _pool is None:
        await init_db_pool()
    
    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                yield conn, cursor
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

async def get_db() -> AsyncGenerator[tuple[aiomysql.Connection, aiomysql.DictCursor], None]:
    """
    FastAPI 의존성(Dependency) 주입용 데이터베이스 연결 생성기.
    요청 당 1연결이 생성되어 반환됨.
    """
    async with get_db_connection() as (conn, cursor):
        yield conn, cursor

# 유틸리티 함수들
async def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """SELECT 쿼리 실행"""
    async with get_db_connection() as (conn, cursor):
        await cursor.execute(query, params)
        return await cursor.fetchall()

async def execute_one(query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """SELECT 쿼리 실행 (단일 결과)"""
    async with get_db_connection() as (conn, cursor):
        await cursor.execute(query, params)
        return await cursor.fetchone()

async def execute_update(query: str, params: tuple = None) -> int:
    """INSERT/UPDATE/DELETE 쿼리 실행"""
    async with get_db_connection() as (conn, cursor):
        await cursor.execute(query, params)
        return cursor.rowcount

async def execute_insert(query: str, params: tuple = None) -> int:
    """INSERT 쿼리 실행 (생성된 ID 반환)"""
    async with get_db_connection() as (conn, cursor):
        await cursor.execute(query, params)
        return cursor.lastrowid