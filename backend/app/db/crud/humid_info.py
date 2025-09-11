from __future__ import annotations
from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.humid_info import HumidInfo


async def get_one(db: AsyncSession, plant_id: int, humid_date: datetime) -> Optional[HumidInfo]:
    res = await db.execute(
        select(HumidInfo).where(
            and_(
                HumidInfo.plant_id == plant_id,
                HumidInfo.humid_date == humid_date,
            )
        )
    )
    return res.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    plant_id: int,
    humid_date: datetime,
    humidity: float,
    dedup: bool = True,
) -> HumidInfo:
    if dedup:
        exists = await get_one(db, plant_id, humid_date)
        if exists:
            return exists
    row = HumidInfo(plant_id=plant_id, humid_date=humid_date, humidity=humidity)
    db.add(row)
    await db.flush()
    return row


async def list_by_plant_cursor(
    db: AsyncSession,
    *,
    plant_id: int,
    limit: int,
    # 커서는 (plant_id 고정 + humid_date/또는 auto pk 역순) 중 하나.
    last_time: datetime | None,
) -> Sequence[HumidInfo]:
    stmt = (
        select(HumidInfo)
        .where(HumidInfo.plant_id == plant_id)
        .order_by(HumidInfo.humid_date.desc())
        .limit(limit + 1)
    )
    if last_time is not None:
        stmt = stmt.where(HumidInfo.humid_date < last_time)
    rows = (await db.execute(stmt)).scalars().all()
    return rows


async def delete_one(db: AsyncSession, plant_id: int, humid_date: datetime) -> int:
    res = await db.execute(
        delete(HumidInfo).where(
            and_(
                HumidInfo.plant_id == plant_id,
                HumidInfo.humid_date == humid_date,
            )
        )
    )
    return res.rowcount or 0
