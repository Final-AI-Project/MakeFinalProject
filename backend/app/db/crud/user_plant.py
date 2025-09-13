from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user_plant import UserPlant


async def get_by_idx(db: AsyncSession, idx: int) -> Optional[UserPlant]:
    res = await db.execute(select(UserPlant).where(UserPlant.idx == idx))
    return res.scalar_one_or_none()


async def get_by_plant_id(db: AsyncSession, plant_id: int) -> Optional[UserPlant]:
    res = await db.execute(select(UserPlant).where(UserPlant.plant_id == plant_id))
    return res.scalar_one_or_none()


async def list_by_user_cursor(
    db: AsyncSession,
    *,
    user_id: str,
    limit: int,
    last_idx: int | None,
) -> Sequence[UserPlant]:
    stmt = (
        select(UserPlant)
        .where(UserPlant.user_id == user_id)
        .order_by(UserPlant.idx.desc())
        .limit(limit + 1)
    )
    if last_idx is not None:
        stmt = stmt.where(UserPlant.idx < last_idx)
    rows = (await db.execute(stmt)).scalars().all()
    return rows


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    plant_id: int,
    plant_name: str,
    species: str | None = None,
    pest_id: int | None = None,
    meet_day=None,
) -> UserPlant:
    up = UserPlant(
        user_id=user_id,
        plant_id=plant_id,
        plant_name=plant_name,
        species=species,
        pest_id=pest_id,
        meet_day=meet_day,
    )
    db.add(up)
    await db.flush()
    return up


async def patch(db: AsyncSession, idx: int, **fields) -> Optional[UserPlant]:
    if fields:
        await db.execute(update(UserPlant).where(UserPlant.idx == idx).values(**fields))
    return await get_by_idx(db, idx)


async def delete_one(db: AsyncSession, idx: int) -> int:
    res = await db.execute(delete(UserPlant).where(UserPlant.idx == idx))
    return res.rowcount or 0
