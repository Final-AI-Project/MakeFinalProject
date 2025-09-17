import aiomysql
from .config import settings

async def get_connection():
    return await aiomysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        db=settings.MYSQL_DB
    )

async def save_chat(species: str, user_content: str, plant_content: str, plant_id: int = None):
    conn = await get_connection()
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO chat_logs (species, plant_id, user_content, plant_content)
            VALUES (%s, %s, %s, %s)
            """,
            (species, plant_id, user_content, plant_content)
        )
    await conn.commit()
    conn.close()
