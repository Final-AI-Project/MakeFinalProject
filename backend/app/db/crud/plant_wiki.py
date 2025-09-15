from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.plant_wiki import PlantWiki


async def get(db: AsyncSession, idx: int) -> Optional[PlantWiki]:
    res = await db.execute(select(PlantWiki).where(PlantWiki.idx == idx))
    return res.scalar_one_or_none()


async def get_by_species(db: AsyncSession, species: str) -> Optional[PlantWiki]:
    res = await db.execute(select(PlantWiki).where(PlantWiki.species == species))
    return res.scalar_one_or_none()


async def create(db: AsyncSession, **fields) -> PlantWiki:
    row = PlantWiki(**fields)
    db.add(row)
    await db.flush()
    return row


async def patch(db: AsyncSession, idx: int, **fields) -> Optional[PlantWiki]:
    if fields:
        await db.execute(update(PlantWiki).where(PlantWiki.idx == idx).values(**fields))
    return await get(db, idx)


async def delete_one(db: AsyncSession, idx: int) -> int:
    res = await db.execute(delete(PlantWiki).where(PlantWiki.idx == idx))
    return res.rowcount or 0


async def list_by_cursor(
    db: AsyncSession,
    *,
    limit: int,
    last_idx: int | None,
) -> Sequence[PlantWiki]:
    stmt = select(PlantWiki).order_by(PlantWiki.idx.desc()).limit(limit + 1)
    if last_idx is not None:
        stmt = stmt.where(PlantWiki.idx < last_idx)
    rows = (await db.execute(stmt)).scalars().all()
    return rows
