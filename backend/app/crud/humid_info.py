from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.humid_info import HumidInfo


async def get_one(db, plant_id: int, humid_date: str) -> Optional[HumidInfo]:
    """특정 날짜의 습도 정보 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            "SELECT * FROM humid_info WHERE plant_id = %s AND humid_date = %s",
            (plant_id, humid_date)
        )
        result = await cursor.fetchone()
        return HumidInfo.from_dict(result) if result else None


async def create(
    db,
    *,
    plant_id: int,
    humidity: float,
    humid_date: str,
) -> HumidInfo:
    """새 습도 정보 생성"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            INSERT INTO humid_info (plant_id, humidity, humid_date)
            VALUES (%s, %s, %s)
            """,
            (plant_id, humidity, humid_date)
        )
        humid_id = cursor.lastrowid
        
        # 생성된 습도 정보 조회
        await cursor.execute("SELECT * FROM humid_info WHERE idx = %s", (humid_id,))
        result = await cursor.fetchone()
        return HumidInfo.from_dict(result)


async def list_by_plant_cursor(
    db,
    plant_id: int,
    *,
    limit: int,
    last_idx: int | None,
) -> List[HumidInfo]:
    """식물별 습도 정보 목록 조회 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        if last_idx is not None:
            await cursor.execute(
                """
                SELECT * FROM humid_info 
                WHERE plant_id = %s AND idx < %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (plant_id, last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                """
                SELECT * FROM humid_info 
                WHERE plant_id = %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (plant_id, limit + 1)
            )
        
        results = await cursor.fetchall()
        return [HumidInfo.from_dict(row) for row in results]


async def delete_one(db, plant_id: int, humid_date: str) -> int:
    """특정 날짜의 습도 정보 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM humid_info WHERE plant_id = %s AND humid_date = %s",
            (plant_id, humid_date)
        )
        return cursor.rowcount
