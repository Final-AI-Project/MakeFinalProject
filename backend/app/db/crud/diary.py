from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.models.diary import Diary


async def get(db: AsyncSession, diary_id: int) -> Optional[Diary]:
    res = await db.execute(
        select(Diary)
        .options(selectinload(Diary.images))
        .where(Diary.diary_id == diary_id)
    )
    return res.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    user_title: str,
    img_url: str | None = None,
    user_content: str | None = None,
    hashtag: str | None = None,
    plant_content: str | None = None,
    weather: str | None = None,
    created_at=None,
) -> Diary:
    d = Diary(
        user_id=user_id,
        user_title=user_title,
        img_url=img_url,
        user_content=user_content,
        hashtag=hashtag,
        plant_content=plant_content,
        weather=weather,
        created_at=created_at,
    )
    db.add(d)
    await db.flush()
    return d


async def patch(db: AsyncSession, diary_id: int, **fields) -> Optional[Diary]:
    if fields:
        await db.execute(
            update(Diary).where(Diary.diary_id == diary_id).values(**fields)
        )
    return await get(db, diary_id)


async def delete_one(db: AsyncSession, diary_id: int) -> int:
    res = await db.execute(delete(Diary).where(Diary.diary_id == diary_id))
    return res.rowcount or 0


async def list_by_user_cursor(
    db: AsyncSession,
    *,
    user_id: str,
    limit: int,
    last_diary_id: int | None,
) -> Sequence[Diary]:
    stmt = (
        select(Diary)
        .options(selectinload(Diary.images))
        .where(Diary.user_id == user_id)
        .order_by(Diary.diary_id.desc())
        .limit(limit + 1)
    )
    if last_diary_id is not None:
        stmt = stmt.where(Diary.diary_id < last_diary_id)
    rows = (await db.execute(stmt)).scalars().all()
    return rows


