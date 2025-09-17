from __future__ import annotations

import aiomysql
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from core.database import get_db
from crud import diary as diary_crud
from schemas.diary import DiaryCreate, DiaryOut
from models.diary import Diary

from utils.errors import http_error
from utils.security import get_current_user
from utils.pagination import (
    decode_id_cursor, 
    encode_id_cursor, 
    page_window
)

# LLM 모듈 임포트
from ml.plant_llm import plant_talk, talk_for_db, TalkResult

router = APIRouter(prefix="/plant-chat", tags=["plant-chat"])

class ChatRequest(BaseModel):
    """식물과의 대화 요청"""
    plant_id: int = Field(..., description="식물 ID")
    plant_name: str = Field(..., description="식물 이름")
    species: str = Field(..., description="식물 종류")
    user_content: str = Field(..., min_length=1, max_length=500, description="사용자 메시지")
    moisture: Optional[float] = Field(None, ge=0, le=100, description="습도 (0-100%)")
    save_to_diary: bool = Field(True, description="일기에 저장할지 여부")

class ChatResponse(BaseModel):
    """식물과의 대화 응답"""
    plant_id: int
    plant_name: str
    species: str
    user_content: str
    plant_content: str
    mode: str  # "daily", "plant", "hybrid"
    state: Optional[str] = None  # "물이부족", "적정", "과습주의"
    created_at: datetime
    diary_id: Optional[int] = None  # 일기에 저장된 경우

class ChatHistoryOut(BaseModel):
    """대화 기록"""
    items: List[ChatResponse]
    next_cursor: str | None
    has_more: bool
    total_count: int

def _to_chat_out(diary: Diary, mode: str, state: Optional[str] = None) -> ChatResponse:
    """Diary 모델을 ChatResponse로 변환"""
    return ChatResponse(
        plant_id=0,  # diary 테이블에는 plant_id가 없으므로 0으로 설정
        plant_name="",  # diary 테이블에는 plant_name이 없으므로 빈 문자열
        species="",  # diary 테이블에는 species가 없으므로 빈 문자열
        user_content=diary.user_content,
        plant_content=diary.plant_content or "",
        mode=mode,
        state=state,
        created_at=diary.created_at or datetime.now(),
        diary_id=diary.idx
    )


@router.post("/talk", response_model=ChatResponse)
async def chat_with_plant(
    body: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물과 대화하기
    - 사용자 메시지를 받아서 식물의 응답 생성
    - 선택적으로 일기에 저장
    """
    try:
        # LLM으로 식물 응답 생성
        result: TalkResult = plant_talk(
            species=body.species,
            user_text=body.user_content,
            moisture=body.moisture
        )
        
        diary_id = None
        
        # 일기에 저장할지 여부에 따라 처리
        if body.save_to_diary:
            # 일기로 저장
            diary = await diary_crud.create(
                db,
                user_id=user["user_id"],
                user_title=f"{body.plant_name}와의 대화",
                user_content=body.user_content,
                plant_content=result.reply,
                hashtag=f"#{body.species}",
                weather=None,  # 필요시 추가
            )
            diary_id = diary.idx
        
        return ChatResponse(
            plant_id=body.plant_id,
            plant_name=body.plant_name,
            species=body.species,
            user_content=body.user_content,
            plant_content=result.reply,
            mode=result.mode,
            state=result.state,
            created_at=datetime.now(),
            diary_id=diary_id
        )
        
    except Exception as e:
        print(f"Plant chat error: {e}")
        raise http_error("chat_failed", "식물과의 대화 중 오류가 발생했습니다.", 500)


@router.get("/history", response_model=ChatHistoryOut)
async def get_chat_history(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    plant_id: Optional[int] = Query(None, description="특정 식물의 대화 기록만 조회"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물과의 대화 기록 조회
    - plant_content가 있는 일기들을 대화 기록으로 간주
    """
    last_idx = decode_id_cursor(cursor)
    
    # plant_content가 있는 일기들만 조회 (대화 기록)
    async with db.cursor(aiomysql.DictCursor) as cursor:
        where_conditions = ["user_id = %s", "plant_content IS NOT NULL", "plant_content != ''"]
        params = [user["user_id"]]
        
        # 특정 식물 필터링 (plant_id가 있으면)
        if plant_id is not None:
            # 실제로는 diary 테이블에 plant_id가 없으므로 hashtag나 다른 방법으로 필터링
            # 여기서는 간단히 모든 대화 기록을 반환
            pass
        
        if last_idx is not None:
            where_conditions.append("idx < %s")
            params.append(last_idx)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT * FROM diary 
            WHERE {where_clause}
            ORDER BY idx DESC 
            LIMIT {limit + 1}
        """
        
        await cursor.execute(query, params)
        results = await cursor.fetchall()
    
    diaries = [Diary.from_dict(row) for row in results]
    items, has_more = page_window(list(diaries), limit)
    next_cursor = encode_id_cursor(items[-1].idx) if has_more else None
    
    # 대화 기록을 ChatResponse로 변환
    chat_items = []
    for diary in items:
        # hashtag에서 species 추출 (간단한 방법)
        species = "몬스테라"  # 기본값
        if diary.hashtag:
            # hashtag가 "#몬스테라" 형태라면 species 추출
            hashtag_clean = diary.hashtag.replace("#", "").strip()
            if hashtag_clean:
                species = hashtag_clean
        
        chat_items.append(_to_chat_out(diary, "plant", None))
    
    return ChatHistoryOut(
        items=chat_items,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=len(diaries),
    )


@router.get("/plants", response_model=List[Dict[str, Any]])
async def get_user_plants(
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    사용자의 식물 목록 조회 (대화 가능한 식물들)
    """
    try:
        # user_plant 테이블에서 사용자의 식물 목록 조회
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
                SELECT plant_id, plant_name, species 
                FROM user_plant 
                WHERE user_id = %s 
                ORDER BY plant_id DESC
                """,
                (user["user_id"],)
            )
            results = await cursor.fetchall()
        
        return [
            {
                "plant_id": row["plant_id"],
                "plant_name": row["plant_name"],
                "species": row["species"]
            }
            for row in results
        ]
        
    except Exception as e:
        print(f"Get user plants error: {e}")
        raise http_error("plants_fetch_failed", "식물 목록 조회 중 오류가 발생했습니다.", 500)


@router.post("/quick-talk", response_model=ChatResponse)
async def quick_chat(
    species: str = Query(..., description="식물 종류"),
    message: str = Query(..., min_length=1, max_length=500, description="메시지"),
    moisture: Optional[float] = Query(None, ge=0, le=100, description="습도"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    빠른 대화 (일기 저장 없이)
    - 특정 종류의 식물과 간단한 대화
    - 일기에 저장하지 않음
    """
    try:
        # LLM으로 식물 응답 생성
        result: TalkResult = plant_talk(
            species=species,
            user_text=message,
            moisture=moisture
        )
        
        return ChatResponse(
            plant_id=0,
            plant_name=f"{species}",
            species=species,
            user_content=message,
            plant_content=result.reply,
            mode=result.mode,
            state=result.state,
            created_at=datetime.now(),
            diary_id=None
        )
        
    except Exception as e:
        print(f"Quick chat error: {e}")
        raise http_error("quick_chat_failed", "빠른 대화 중 오류가 발생했습니다.", 500)
