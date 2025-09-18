import aiomysql
from datetime import datetime
from .config import settings

async def get_connection():
    return await aiomysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        db=settings.MYSQL_DB
    )

async def save_chat(chat_data: dict):
    """
    ERD의 diary 테이블에 채팅 내용을 저장합니다.
    
    Args:
        chat_data: talk_for_db()에서 반환된 딕셔너리
    """
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO diary (
                    user_id, 
                    user_title, 
                    user_content, 
                    hashtag, 
                    plant_content, 
                    weather, 
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    chat_data["user_id"],
                    chat_data["user_title"],
                    chat_data["user_content"],
                    chat_data["hashtag"],
                    chat_data["plant_content"],
                    chat_data["weather"],
                    datetime.now()
                )
            )
            diary_id = cur.lastrowid
            await conn.commit()
            return diary_id
    except Exception as e:
        await conn.rollback()
        raise e
    finally:
        conn.close()

async def get_chat_history(user_id: str, limit: int = 10):
    """
    사용자의 최근 채팅 기록을 조회합니다.
    """
    conn = await get_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT 
                    diary_id,
                    user_title,
                    user_content,
                    plant_content,
                    hashtag,
                    weather,
                    created_at
                FROM diary 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """,
                (user_id, limit)
            )
            results = await cur.fetchall()
            return results
    except Exception as e:
        raise e
    finally:
        conn.close()
