"""
공통 의존성 (Depends) 모듈
"""
from fastapi import Depends, HTTPException, status
from typing import Generator, Dict, Any
import aiomysql

from db.pool import get_db_connection
from services.auth_service import get_current_user


def get_db() -> Generator[aiomysql.Connection, None, None]:
    """
    데이터베이스 연결 의존성
    """
    async with get_db_connection() as (conn, cursor):
        yield conn


def get_current_user_dependency() -> Dict[str, Any]:
    """
    현재 사용자 인증 의존성
    """
    return get_current_user


# 기존 시그니처 유지를 위한 별칭
get_current_user_dep = get_current_user_dependency
