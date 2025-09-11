from __future__ import annotations
from typing import  Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.img_address import ImgAddress


async def add_image_url(
    db: AsyncSession,
    *,
    diary_id: int,
    img_url: str,
) -> ImgAddress:
    img = ImgAddress(diary_id=diary_id, img_url=img_url)
    db.add(img)
    await db.flush()
    return img


async def list_images(db: AsyncSession, diary_id: int) -> Sequence[ImgAddress]:
    res = await db.execute(select(ImgAddress).where(ImgAddress.diary_id == diary_id))
    return res.scalars().all()


async def delete_image(db: AsyncSession, idx: int) -> int:
    res = await db.execute(delete(ImgAddress).where(ImgAddress.idx == idx))
    return res.rowcount or 0
