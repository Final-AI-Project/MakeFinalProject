from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.diary import Diary


async def get_by_idx(db, idx: int) -> Optional[Diary]:
    """idx로 일기 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM diary WHERE idx = %s", (idx,))
        result = await cursor.fetchone()
        return Diary.from_dict(result) if result else None


async def create(
    db,
    *,
    user_id: str,
    user_title: str,
    user_content: str,
    img_url: Optional[str] = None,
    hashtag: Optional[str] = None,
    plant_content: Optional[str] = None,
    weather: Optional[str] = None,
) -> Diary:
    """새 일기 생성"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            INSERT INTO diary (user_id, user_title, img_url, user_content, hashtag, plant_content, weather, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (user_id, user_title, img_url, user_content, hashtag, plant_content, weather)
        )
        diary_id = cursor.lastrowid
        
        # 생성된 일기 조회
        await cursor.execute("SELECT * FROM diary WHERE idx = %s", (diary_id,))
        result = await cursor.fetchone()
        return Diary.from_dict(result)


async def patch(
    db,
    idx: int,
    **fields,
) -> Optional[Diary]:
    """일기 수정"""
    if not fields:
        return await get_by_idx(db, idx)
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    
    values.append(idx)
    query = f"UPDATE diary SET {', '.join(set_clauses)} WHERE idx = %s"
    
    async with db.cursor() as cursor:
        await cursor.execute(query, values)
        
    # 수정된 일기 조회
    return await get_by_idx(db, idx)


async def delete_by_idx(db, idx: int) -> int:
    """일기 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM diary WHERE idx = %s", (idx,))
        return cursor.rowcount


async def list_by_user_cursor(
    db,
    user_id: str,
    *,
    limit: int,
    last_idx: int | None,
) -> List[Diary]:
    """사용자별 일기 목록 조회 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        if last_idx is not None:
            await cursor.execute(
                """
                SELECT * FROM diary 
                WHERE user_id = %s AND idx < %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (user_id, last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                """
                SELECT * FROM diary 
                WHERE user_id = %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (user_id, limit + 1)
            )
        
        results = await cursor.fetchall()
        return [Diary.from_dict(row) for row in results]
