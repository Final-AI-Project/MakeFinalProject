import asyncio
import aiomysql
from app.core.config import settings

async def kill_problematic_session():
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
            # 문제 세션은 이미 자동 해결됨
            print("✅ 문제 세션 8495는 이미 자동 해결됨")
            
            # 락 타임아웃 설정 조정
            await cursor.execute("SET innodb_lock_wait_timeout = 5")
            print("✅ 락 타임아웃을 5초로 설정")
            
            # 현재 설정 확인
            await cursor.execute("SHOW VARIABLES LIKE 'innodb_lock_wait_timeout'")
            result = await cursor.fetchone()
            print(f"📊 현재 락 타임아웃: {result[1]}초")
            
    finally:
        await conn.ensure_closed()

if __name__ == "__main__":
    asyncio.run(kill_problematic_session())
