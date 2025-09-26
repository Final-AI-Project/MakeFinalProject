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

async def init_pool():
    """데이터베이스 연결 풀 초기화"""
    global _pool
    if _pool is None:
        config = _get_mysql_config()
        try:
            _pool = await aiomysql.create_pool(**config)
            print(f"[DB] host = '{config['host']}'")
        except Exception as e:
            print(f"[DB] 연결 실패: {e}")
            raise
    return _pool

async def get_pool() -> aiomysql.Pool:
    """연결 풀 반환"""
    if _pool is None:
        await init_pool()
    return _pool

async def recreate_pool():
    """연결 풀 재생성 (연결 문제 해결용)"""
    global _pool
    if _pool:
        try:
            _pool.close()
            await _pool.wait_closed()
        except Exception as e:
            print(f"[DB] 기존 풀 종료 중 오류: {e}")
        _pool = None
    await init_pool()

async def close_pool():
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
        await init_pool()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with _pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    try:
                        yield conn, cursor
                        await conn.commit()
                        return
                    except Exception as e:
                        # 연결 상태를 확인하고 안전하게 rollback
                        try:
                            if conn and hasattr(conn, '_closed') and not conn._closed:
                                await conn.rollback()
                        except Exception as rollback_error:
                            print(f"Rollback failed: {rollback_error}")
                        raise e
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[DB] 연결 시도 {attempt + 1} 실패, 재시도 중...: {e}")
                await recreate_pool()
                continue
            else:
                print(f"[DB] 최대 재시도 횟수 초과: {e}")
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
