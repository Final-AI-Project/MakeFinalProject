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
    plant_nickname: Optional[str] = None,
    plant_species: Optional[str] = None,
    plant_reply: Optional[str] = None,
    weather: Optional[str] = None,
    weather_icon: Optional[str] = None,
) -> Diary:
    """새 일기 생성"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # 1. diary 테이블에 일기 생성 (최소한의 컬럼만 사용)
        await cursor.execute(
            """
            INSERT INTO diary (user_id, user_title, user_content)
            VALUES (%s, %s, %s)
            """,
            (user_id, user_title, user_content)
        )
        diary_id = cursor.lastrowid
        
        # 2. 이미지가 있으면 img_address 테이블에 저장 (idx를 diary_id로 사용)
        if img_url:
            await cursor.execute(
                """
                INSERT INTO img_address (diary_id, img_url)
                VALUES (%s, %s)
                """,
                (diary_id, img_url)
            )
        
        # 3. 생성된 일기 조회 (idx 사용)
        await cursor.execute("SELECT * FROM diary WHERE idx = %s", (diary_id,))
        result = await cursor.fetchone()
        if not result:
            # idx가 없으면 다른 방법으로 조회
            await cursor.execute("SELECT * FROM diary ORDER BY idx DESC LIMIT 1")
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
    
    # updated_at 필드 자동 추가
    fields['updated_at'] = 'NOW()'
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        if key == 'updated_at':
            set_clauses.append(f"{key} = {value}")
        else:
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
