"""
aiomysql 연결 풀 관리
"""
import aiomysql
from typing import Optional
from core.config import settings

_pool: Optional[aiomysql.Pool] = None

async def init_pool():
    """데이터베이스 연결 풀 초기화"""
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=str(settings.DB_HOST),
            port=settings.DB_PORT,
            user=str(settings.DB_USER),
            password=str(settings.DB_PASSWORD),
            db=str(settings.DB_NAME),
            charset='utf8mb4',
            autocommit=True,
            minsize=1,
            maxsize=10
        )

async def get_pool() -> aiomysql.Pool:
    """연결 풀 반환"""
    if _pool is None:
        await init_pool()
    return _pool

async def get_db_connection():
    """데이터베이스 연결 반환"""
    pool = await get_pool()
    return await pool.acquire()

async def close_pool():
    """연결 풀 종료"""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
