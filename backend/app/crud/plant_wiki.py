from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.plant_wiki import PlantWiki


async def get_by_idx(db, idx: int) -> Optional[PlantWiki]:
    """idx로 식물 위키 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM plant_wiki WHERE idx = %s", (idx,))
        result = await cursor.fetchone()
        return PlantWiki.from_dict(result) if result else None


async def get_by_species(db, species: str) -> Optional[PlantWiki]:
    """species로 식물 위키 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM plant_wiki WHERE species = %s", (species,))
        result = await cursor.fetchone()
        return PlantWiki.from_dict(result) if result else None


async def create(
    db,
    *,
    species: str,
    wiki_image: Optional[str] = None,
    sunlight: Optional[str] = None,
    watering: Optional[str] = None,
    flowering: Optional[str] = None,
    fertilizer: Optional[str] = None,
    toxicity: Optional[str] = None,
) -> PlantWiki:
    """새 식물 위키 생성"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            INSERT INTO plant_wiki (species, wiki_image, sunlight, watering, flowering, fertilizer, toxicity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (species, wiki_image, sunlight, watering, flowering, fertilizer, toxicity)
        )
        wiki_id = cursor.lastrowid
        
        # 생성된 위키 조회
        await cursor.execute("SELECT * FROM plant_wiki WHERE idx = %s", (wiki_id,))
        result = await cursor.fetchone()
        return PlantWiki.from_dict(result)


async def patch(
    db,
    idx: int,
    **fields,
) -> Optional[PlantWiki]:
    """식물 위키 수정"""
    if not fields:
        return await get_by_idx(db, idx)
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    
    values.append(idx)
    query = f"UPDATE plant_wiki SET {', '.join(set_clauses)} WHERE idx = %s"
    
    async with db.cursor() as cursor:
        await cursor.execute(query, values)
        
    # 수정된 위키 조회
    return await get_by_idx(db, idx)


async def delete_by_idx(db, idx: int) -> int:
    """식물 위키 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM plant_wiki WHERE idx = %s", (idx,))
        return cursor.rowcount


async def list_by_cursor(
    db,
    *,
    limit: int,
    last_idx: int | None,
) -> List[PlantWiki]:
    """식물 위키 목록 조회 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        if last_idx is not None:
            await cursor.execute(
                "SELECT * FROM plant_wiki WHERE idx < %s ORDER BY idx DESC LIMIT %s",
                (last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                "SELECT * FROM plant_wiki ORDER BY idx DESC LIMIT %s",
                (limit + 1,)
            )
        
        results = await cursor.fetchall()
        return [PlantWiki.from_dict(row) for row in results]


async def search_by_species(
    db,
    *,
    search_term: str,
    limit: int,
    last_idx: int | None,
) -> List[PlantWiki]:
    """식물 종류로 검색 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        search_pattern = f"%{search_term}%"
        
        if last_idx is not None:
            await cursor.execute(
                "SELECT * FROM plant_wiki WHERE species LIKE %s AND idx < %s ORDER BY idx DESC LIMIT %s",
                (search_pattern, last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                "SELECT * FROM plant_wiki WHERE species LIKE %s ORDER BY idx DESC LIMIT %s",
                (search_pattern, limit + 1)
            )
        
        results = await cursor.fetchall()
        return [PlantWiki.from_dict(row) for row in results]


async def get_by_category(
    db,
    *,
    category: str,
    limit: int,
) -> List[PlantWiki]:
    """특정 카테고리 정보가 있는 식물들 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # 해당 카테고리 필드가 NULL이 아닌 식물들만 조회
        await cursor.execute(
            f"SELECT * FROM plant_wiki WHERE {category} IS NOT NULL ORDER BY idx DESC LIMIT %s",
            (limit,)
        )
        
        results = await cursor.fetchall()
        return [PlantWiki.from_dict(row) for row in results]
