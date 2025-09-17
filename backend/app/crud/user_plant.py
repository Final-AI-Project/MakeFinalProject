from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.user_plant import UserPlant


async def get_by_idx(db, idx: int) -> Optional[UserPlant]:
    """idx로 식물 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_plant WHERE idx = %s", (idx,))
        result = await cursor.fetchone()
        return UserPlant.from_dict(result) if result else None


async def get_by_plant_id(db, plant_id: int) -> Optional[UserPlant]:
    """plant_id로 식물 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_plant WHERE plant_id = %s", (plant_id,))
        result = await cursor.fetchone()
        return UserPlant.from_dict(result) if result else None


async def list_by_user_cursor(
    db,
    user_id: str,
    *,
    limit: int,
    last_idx: int | None,
) -> List[UserPlant]:
    """사용자별 식물 목록 조회 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        if last_idx is not None:
            await cursor.execute(
                """
                SELECT * FROM user_plant 
                WHERE user_id = %s AND idx < %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (user_id, last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                """
                SELECT * FROM user_plant 
                WHERE user_id = %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (user_id, limit + 1)
            )
        
        results = await cursor.fetchall()
        return [UserPlant.from_dict(row) for row in results]


async def create(
    db,
    *,
    user_id: str,
    plant_name: str,
    species: Optional[str] = None,
    pest_id: Optional[int] = None,
    meet_day: Optional[str] = None,
) -> UserPlant:
    """새 식물 등록"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # plant_id 자동 생성 (현재 최대값 + 1)
        await cursor.execute("SELECT COALESCE(MAX(plant_id), 0) + 1 as next_id FROM user_plant")
        result = await cursor.fetchone()
        plant_id = result["next_id"]
        
        await cursor.execute(
            """
            INSERT INTO user_plant (user_id, plant_id, plant_name, species, pest_id, meet_day)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, plant_id, plant_name, species, pest_id, meet_day)
        )
        
        # 생성된 식물 조회
        await cursor.execute("SELECT * FROM user_plant WHERE plant_id = %s", (plant_id,))
        result = await cursor.fetchone()
        return UserPlant.from_dict(result)


async def patch(
    db,
    plant_id: int,
    **fields,
) -> Optional[UserPlant]:
    """식물 정보 수정"""
    if not fields:
        return await get_by_plant_id(db, plant_id)
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    
    values.append(plant_id)
    query = f"UPDATE user_plant SET {', '.join(set_clauses)} WHERE plant_id = %s"
    
    async with db.cursor() as cursor:
        await cursor.execute(query, values)
        
    # 수정된 식물 조회
    return await get_by_plant_id(db, plant_id)


async def delete_by_plant_id(db, plant_id: int) -> int:
    """식물 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM user_plant WHERE plant_id = %s", (plant_id,))
        return cursor.rowcount
