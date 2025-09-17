from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.pest_wiki import PestWiki


async def get_by_idx(db, idx: int) -> Optional[PestWiki]:
    """idx로 해충 위키 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM pest_wiki WHERE idx = %s", (idx,))
        result = await cursor.fetchone()
        return PestWiki.from_dict(result) if result else None


async def get_by_pest_id(db, pest_id: int) -> Optional[PestWiki]:
    """pest_id로 해충 위키 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM pest_wiki WHERE pest_id = %s", (pest_id,))
        result = await cursor.fetchone()
        return PestWiki.from_dict(result) if result else None


async def create(
    db,
    *,
    pest_id: int,
    cause: Optional[str] = None,
    cure: Optional[str] = None,
) -> PestWiki:
    """새 해충 위키 생성"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            INSERT INTO pest_wiki (pest_id, cause, cure)
            VALUES (%s, %s, %s)
            """,
            (pest_id, cause, cure)
        )
        wiki_id = cursor.lastrowid
        
        # 생성된 위키 조회
        await cursor.execute("SELECT * FROM pest_wiki WHERE idx = %s", (wiki_id,))
        result = await cursor.fetchone()
        return PestWiki.from_dict(result)


async def patch(
    db,
    idx: int,
    **fields,
) -> Optional[PestWiki]:
    """해충 위키 수정"""
    if not fields:
        return await get_by_idx(db, idx)
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    
    values.append(idx)
    query = f"UPDATE pest_wiki SET {', '.join(set_clauses)} WHERE idx = %s"
    
    async with db.cursor() as cursor:
        await cursor.execute(query, values)
        
    # 수정된 위키 조회
    return await get_by_idx(db, idx)


async def delete_by_idx(db, idx: int) -> int:
    """해충 위키 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM pest_wiki WHERE idx = %s", (idx,))
        return cursor.rowcount


async def list_by_cursor(
    db,
    *,
    limit: int,
    last_idx: int | None,
) -> List[PestWiki]:
    """해충 위키 목록 조회 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        if last_idx is not None:
            await cursor.execute(
                "SELECT * FROM pest_wiki WHERE idx < %s ORDER BY idx DESC LIMIT %s",
                (last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                "SELECT * FROM pest_wiki ORDER BY idx DESC LIMIT %s",
                (limit + 1,)
            )
        
        results = await cursor.fetchall()
        return [PestWiki.from_dict(row) for row in results]
