from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.img_address import ImgAddress


async def get_by_idx(db, idx: int) -> Optional[ImgAddress]:
    """idx로 이미지 주소 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM img_address WHERE idx = %s", (idx,))
        result = await cursor.fetchone()
        return ImgAddress.from_dict(result) if result else None


async def list_by_diary_id(db, diary_id: int) -> List[ImgAddress]:
    """일기별 이미지 주소 목록 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            "SELECT * FROM img_address WHERE diary_id = %s ORDER BY idx",
            (diary_id,)
        )
        results = await cursor.fetchall()
        return [ImgAddress.from_dict(row) for row in results]


async def create(
    db,
    *,
    diary_id: int,
    img_url: str,
    status: int | None = None,
) -> ImgAddress:
    """새 이미지 주소 생성"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            INSERT INTO img_address (diary_id, img_url, status)
            VALUES (%s, %s, %s)
            """,
            (diary_id, img_url, status)
        )
        img_id = cursor.lastrowid
        
        # 생성된 이미지 주소 조회
        await cursor.execute("SELECT * FROM img_address WHERE idx = %s", (img_id,))
        result = await cursor.fetchone()
        return ImgAddress.from_dict(result)


async def delete_by_idx(db, idx: int) -> int:
    """이미지 주소 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM img_address WHERE idx = %s", (idx,))
        return cursor.rowcount


async def delete_by_diary_id(db, diary_id: int) -> int:
    """일기별 모든 이미지 주소 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM img_address WHERE diary_id = %s", (diary_id,))
        return cursor.rowcount
