from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User


async def get_by_idx(db: AsyncSession, idx: int) -> Optional[User]:
    res = await db.execute(select(User).where(User.idx == idx))
    return res.scalar_one_or_none()


async def get_by_user_id(db: AsyncSession, user_id: str) -> Optional[User]:
    res = await db.execute(select(User).where(User.user_id == user_id))
    return res.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    hashed_pw: str,
    email: str,
    hp: str,
    nickname: str,
) -> User:
    u = User(
        user_id=user_id,
        user_pw=hashed_pw,
        email=email,
        hp=hp,
        nickname=nickname,
    )
    db.add(u)
    await db.flush()
    return u


async def patch(
    db: AsyncSession,
    idx: int,
    **fields,
) -> Optional[User]:
    if not fields:
        return await get_by_idx(db, idx)
    await db.execute(update(User).where(User.idx == idx).values(**fields))
    # 갱신된 행 재조회
    return await get_by_idx(db, idx)


async def delete_by_idx(db: AsyncSession, idx: int) -> int:
    res = await db.execute(delete(User).where(User.idx == idx))
    return res.rowcount or 0


async def list_by_cursor(
    db: AsyncSession,
    *,
    limit: int,
    last_idx: int | None,
) -> Sequence[User]:
    stmt = select(User).order_by(User.idx.desc()).limit(limit + 1)
    if last_idx is not None:
        stmt = stmt.where(User.idx < last_idx)
    rows = (await db.execute(stmt)).scalars().all()
    return rows
