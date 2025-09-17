#!/usr/bin/env python3
"""
SQLite 데이터베이스 테이블 생성 스크립트
개발용으로 사용
"""

import asyncio
from core.database import engine, Base
# 모든 모델을 import (관계 설정을 위해 필요)
from db.models import *

async def create_tables():
    """모든 테이블을 생성합니다."""
    print("데이터베이스 테이블을 생성하는 중...")
    
    async with engine.begin() as conn:
        # 모든 테이블 생성
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
    print("📁 데이터베이스 파일: backend/app/dev.db")

if __name__ == "__main__":
    asyncio.run(create_tables())
