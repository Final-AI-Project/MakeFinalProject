"""
DB 연결 테스트 스크립트
"""
import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.pool import init_pool, close_pool, get_db_connection
from core.config import settings

async def test_db_connection():
    """DB 연결 테스트"""
    print("🔍 DB 연결 테스트 시작...")
    print(f"📍 DB 호스트: {settings.DB_HOST}")
    print(f"📍 DB 포트: {settings.DB_PORT}")
    print(f"📍 DB 사용자: {settings.DB_USER}")
    print(f"📍 DB 이름: {settings.DB_NAME}")
    print("-" * 50)
    
    try:
        # 1. DB 연결 풀 초기화 테스트
        print("1️⃣ DB 연결 풀 초기화 중...")
        await init_pool()
        print("✅ DB 연결 풀 초기화 성공!")
        
        # 2. DB 연결 테스트
        print("2️⃣ DB 연결 테스트 중...")
        async with get_db_connection() as (conn, cursor):
            print("✅ DB 연결 성공!")
            
            # 3. 간단한 쿼리 테스트
            print("3️⃣ 쿼리 실행 테스트 중...")
            await cursor.execute("SELECT 1 as test")
            result = await cursor.fetchone()
            print(f"✅ 쿼리 실행 성공! 결과: {result}")
            
            # 4. 현재 시간 조회 테스트
            print("4️⃣ 현재 시간 조회 테스트 중...")
            await cursor.execute("SELECT NOW() as now_time")
            result = await cursor.fetchone()
            print(f"✅ 현재 시간: {result['now_time']}")
            
            # 5. 데이터베이스 정보 조회
            print("5️⃣ 데이터베이스 정보 조회 중...")
            await cursor.execute("SELECT DATABASE() as db_name, USER() as user_name")
            result = await cursor.fetchone()
            print(f"✅ 데이터베이스: {result['db_name']}")
            print(f"✅ 사용자: {result['user_name']}")
            
            # 6. 테이블 목록 조회
            print("6️⃣ 테이블 목록 조회 중...")
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            print(f"✅ 테이블 개수: {len(tables)}")
            if tables:
                print("📋 테이블 목록:")
                for table in tables[:10]:  # 최대 10개만 표시
                    table_name = list(table.values())[0]
                    print(f"   - {table_name}")
                if len(tables) > 10:
                    print(f"   ... 외 {len(tables) - 10}개")
        
        # 7. 연결 풀 종료
        print("7️⃣ DB 연결 풀 종료 중...")
        await close_pool()
        print("✅ DB 연결 풀 종료 완료!")
        
        print("\n🎉 모든 DB 연결 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"\n❌ DB 연결 테스트 실패!")
        print(f"오류 타입: {type(e).__name__}")
        print(f"오류 메시지: {str(e)}")
        
        # 연결 풀 정리
        try:
            await close_pool()
        except:
            pass
            
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Pland Backend DB 연결 테스트")
    print("=" * 60)
    
    # DB 연결 테스트 실행
    success = asyncio.run(test_db_connection())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DB 연결 테스트 완료 - 모든 테스트 통과!")
    else:
        print("💥 DB 연결 테스트 실패 - 설정을 확인해주세요!")
    print("=" * 60)
