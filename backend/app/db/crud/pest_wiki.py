from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.pest_wiki import PestWiki


async def get(db: AsyncSession, idx: int) -> Optional[PestWiki]:
    res = await db.execute(select(PestWiki).where(PestWiki.idx == idx))
    return res.scalar_one_or_none()


async def get_by_pest_id(db: AsyncSession, pest_id: int) -> Optional[PestWiki]:
    res = await db.execute(select(PestWiki).where(PestWiki.pest_id == pest_id))
    return res.scalar_one_or_none()


async def create(db: AsyncSession, **fields) -> PestWiki:
    row = PestWiki(**fields)
    db.add(row)
    await db.flush()
    return row


async def patch(db: AsyncSession, idx: int, **fields) -> Optional[PestWiki]:
    if fields:
        await db.execute(update(PestWiki).where(PestWiki.idx == idx).values(**fields))
    return await get(db, idx)


async def delete_one(db: AsyncSession, idx: int) -> int:
    res = await db.execute(delete(PestWiki).where(PestWiki.idx == idx))
    return res.rowcount or 0


async def list_by_cursor(
    db: AsyncSession,
    *,
    limit: int,
    last_idx: int | None,
) -> Sequence[PestWiki]:
    stmt = select(PestWiki).order_by(PestWiki.idx.desc()).limit(limit + 1)
    if last_idx is not None:
        stmt = stmt.where(PestWiki.idx < last_idx)
    rows = (await db.execute(stmt)).scalars().all()
    return rows
