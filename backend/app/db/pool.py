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
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
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

async def close_pool():
    """연결 풀 종료"""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
