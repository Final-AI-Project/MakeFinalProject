import asyncio
import aiomysql
from app.core.config import settings

async def check_locks():
    conn = await aiomysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD.get_secret_value(),
        db=settings.DB_NAME,
        charset='utf8mb4'
    )
    try:
        async with conn.cursor() as cursor:
            # 권한이 없는 경우 대체 방법으로 락 확인
            print("🔍 권한 제한으로 인해 performance_schema 접근 불가")
            print("📋 대체 방법으로 락 상태 확인 중...")
            
            # 1. SHOW PROCESSLIST로 활성 세션 확인
            await cursor.execute("SHOW PROCESSLIST")
            processes = await cursor.fetchall()
            
            print("\n🔄 현재 활성 프로세스들:")
            for process in processes:
                if process[3] == 'Final' and process[4] != 'Sleep':  # Final DB, Sleep이 아닌 것만
                    print(f"  - ID: {process[0]}, User: {process[1]}, Host: {process[2]}")
                    print(f"    DB: {process[3]}, Command: {process[4]}, Time: {process[5]}s")
                    print(f"    State: {process[6]}")
                    if process[7]:  # Info (쿼리)
                        print(f"    Query: {process[7][:100]}...")
                    print()
            
            # 2. 현재 트랜잭션 상태 확인
            await cursor.execute("SELECT @@autocommit, @@tx_isolation")
            tx_info = await cursor.fetchone()
            print(f"📊 트랜잭션 설정: autocommit={tx_info[0]}, isolation={tx_info[1]}")
            
            # 3. 락 타임아웃 설정 확인
            await cursor.execute("SHOW VARIABLES LIKE 'innodb_lock_wait_timeout'")
            timeout_info = await cursor.fetchone()
            print(f"⏰ 락 타임아웃: {timeout_info[1]}초")
                
    finally:
        await conn.ensure_closed()

if __name__ == "__main__":
    asyncio.run(check_locks())
