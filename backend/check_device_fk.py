import asyncio
import aiomysql
from app.core.config import settings

async def check_device_fk():
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
            # device_info 테이블에서 idx=21 확인
            await cursor.execute('SELECT idx, plant_id, device_id FROM device_info WHERE idx = 21')
            result = await cursor.fetchone()
            if result:
                print(f'✅ device_fk=21 존재: {result}')
            else:
                print('❌ device_fk=21 미존재')
                # 전체 device_info 확인
                await cursor.execute('SELECT idx, plant_id, device_id FROM device_info LIMIT 10')
                all_devices = await cursor.fetchall()
                print(f'📋 사용 가능한 device_fk: {all_devices}')
    finally:
        await conn.ensure_closed()

if __name__ == "__main__":
    asyncio.run(check_device_fk())
