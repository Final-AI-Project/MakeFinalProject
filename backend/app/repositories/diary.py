from __future__ import annotations
from typing import Optional, List, Dict, Any
import aiomysql

from models.diary import Diary


async def get_by_idx(db, idx: int) -> Optional[Diary]:
    """idx로 일기 조회"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM diary WHERE idx = %s", (idx,))
        result = await cursor.fetchone()
        return Diary.from_dict(result) if result else None


async def create(
    db,
    *,
    user_id: str,
    user_title: str,
    user_content: str,
    img_url: Optional[str] = None,
    hashtag: Optional[str] = None,
    plant_nickname: Optional[str] = None,
    plant_species: Optional[str] = None,
    plant_reply: Optional[str] = None,
    weather: Optional[str] = None,
    weather_icon: Optional[str] = None,
) -> Diary:
    """새 일기 생성"""
    print(f"[DEBUG] create_diary 호출됨 - user_id: {user_id}")
    print(f"[DEBUG] 데이터: title={user_title}, content={user_content[:50]}..., weather={weather}")
    
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # 1. diary 테이블에 일기 생성
        print("[DEBUG] diary 테이블에 INSERT 시도")
        try:
            await cursor.execute(
                """
                INSERT INTO diary (user_id, user_title, user_content, hashtag, plant_nickname, plant_species, plant_reply, weather, weather_icon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, user_title, user_content, hashtag, plant_nickname, plant_species, plant_reply, weather, weather_icon)
            )
            diary_id = cursor.lastrowid
            print(f"[DEBUG] diary INSERT 성공 - diary_id: {diary_id}")
        except Exception as e:
            print(f"[DEBUG] diary INSERT 실패: {e}")
            print(f"[DEBUG] INSERT 데이터: user_id={user_id}, title={user_title}, content={user_content[:50]}...")
            raise e
        
        # 2. 이미지가 있으면 img_address 테이블에 저장 (idx를 diary_id로 사용)
        if img_url:
            print(f"[DEBUG] img_address 테이블에 INSERT 시도 - diary_id: {diary_id}")
            await cursor.execute(
                """
                INSERT INTO img_address (diary_id, img_url)
                VALUES (%s, %s)
                """,
                (diary_id, img_url)
            )
            print("[DEBUG] img_address INSERT 성공")
        
        # 3. 생성된 일기 조회 (idx 사용)
        print(f"[DEBUG] 생성된 일기 조회 시도 - idx: {diary_id}")
        await cursor.execute("SELECT * FROM diary WHERE idx = %s", (diary_id,))
        result = await cursor.fetchone()
        if not result:
            print("[DEBUG] idx로 조회 실패, 최신 일기로 조회 시도")
            # idx가 없으면 다른 방법으로 조회
            await cursor.execute("SELECT * FROM diary ORDER BY idx DESC LIMIT 1")
            result = await cursor.fetchone()
        
        if result:
            print(f"[DEBUG] 일기 조회 성공: {result}")
            return Diary.from_dict(result)
        else:
            print("[DEBUG] 일기 조회 실패")
            raise Exception("생성된 일기를 조회할 수 없습니다")


async def patch(
    db,
    idx: int,
    **fields,
) -> Optional[Diary]:
    """일기 수정"""
    if not fields:
        return await get_by_idx(db, idx)
    
    # updated_at 필드 자동 추가
    fields['updated_at'] = 'NOW()'
    
    # 동적으로 UPDATE 쿼리 생성
    set_clauses = []
    values = []
    for key, value in fields.items():
        if key == 'updated_at':
            set_clauses.append(f"{key} = {value}")
        else:
            set_clauses.append(f"{key} = %s")
            values.append(value)
    
    values.append(idx)
    query = f"UPDATE diary SET {', '.join(set_clauses)} WHERE idx = %s"
    
    async with db.cursor() as cursor:
        await cursor.execute(query, values)
        
    # 수정된 일기 조회
    return await get_by_idx(db, idx)


async def delete_by_idx(db, idx: int) -> int:
    """일기 삭제"""
    async with db.cursor() as cursor:
        await cursor.execute("DELETE FROM diary WHERE idx = %s", (idx,))
        return cursor.rowcount


async def list_by_user_cursor(
    db,
    user_id: str,
    *,
    limit: int,
    last_idx: int | None,
) -> List[Diary]:
    """사용자별 일기 목록 조회 (커서 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        if last_idx is not None:
            await cursor.execute(
                """
                SELECT * FROM diary 
                WHERE user_id = %s AND idx < %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (user_id, last_idx, limit + 1)
            )
        else:
            await cursor.execute(
                """
                SELECT * FROM diary 
                WHERE user_id = %s 
                ORDER BY idx DESC LIMIT %s
                """,
                (user_id, limit + 1)
            )
        
        results = await cursor.fetchall()
        return [Diary.from_dict(row) for row in results]
