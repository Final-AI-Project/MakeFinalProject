from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.user import User


async def get_by_idx(db, idx: int) -> Optional[User]:
    """idx로 사용자 조회"""
    conn, cursor = db
    await cursor.execute("SELECT * FROM users WHERE idx = %s", (idx,))
    result = await cursor.fetchone()
    return User.from_dict(result) if result else None


async def get_by_user_id(db, user_id: str) -> Optional[User]:
    """user_id로 사용자 조회"""
    conn, cursor = db
    await cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    result = await cursor.fetchone()
    return User.from_dict(result) if result else None


async def get_by_email(db, email: str) -> Optional[User]:
    """email로 사용자 조회"""
    conn, cursor = db
    await cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    result = await cursor.fetchone()
    return User.from_dict(result) if result else None


async def get_by_hp(db, hp: str) -> Optional[User]:
    """hp로 사용자 조회"""
    conn, cursor = db
    await cursor.execute("SELECT * FROM users WHERE hp = %s", (hp,))
    result = await cursor.fetchone()
    return User.from_dict(result) if result else None


async def create(
    db,
    *,
    user_id: str,
    hashed_pw: str,
    email: str,
    hp: str,
    nickname: str,
) -> User:
    """새 사용자 생성"""
    conn, cursor = db
    await cursor.execute(
        """
        INSERT INTO users (user_id, user_pw, email, hp, nickname, regdate)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """,
        (user_id, hashed_pw, email, hp, nickname)
    )
    user_id_val = cursor.lastrowid
    
    # 생성된 사용자 조회
    await cursor.execute("SELECT * FROM users WHERE idx = %s", (user_id_val,))
    result = await cursor.fetchone()
    return User.from_dict(result)


async def patch(
    db,
    idx: int,
    **fields,
) -> Optional[User]:
    """사용자 정보 수정"""
    if not fields:
        return await get_by_idx(db, idx)
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)
    
    values.append(idx)
    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE idx = %s"
    
    conn, cursor = db
    await cursor.execute(query, values)
        
    # 수정된 사용자 조회
    return await get_by_idx(db, idx)


async def delete_by_idx(db, idx: int) -> int:
    """사용자 삭제"""
    conn, cursor = db
    await cursor.execute("DELETE FROM users WHERE idx = %s", (idx,))
    return cursor.rowcount


async def list_by_cursor(
    db,
    *,
    limit: int,
    last_idx: int | None,
) -> List[User]:
    """커서 기반 사용자 목록 조회"""
    conn, cursor = db
    if last_idx is not None:
        await cursor.execute(
            "SELECT * FROM users WHERE idx < %s ORDER BY idx DESC LIMIT %s",
            (last_idx, limit + 1)
        )
    else:
        await cursor.execute(
            "SELECT * FROM users ORDER BY idx DESC LIMIT %s",
            (limit + 1,)
        )
    
    results = await cursor.fetchall()
    return [User.from_dict(row) for row in results]
