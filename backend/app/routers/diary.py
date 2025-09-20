from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
import json

from schemas.diary import (
    DiaryCreate, DiaryUpdate, DiaryOut, DiaryListOut, 
    DiaryWriteRequest, DiaryWriteResponse, DiaryStatsResponse
)
from repositories.diary import (
    create_diary, get_user_diaries, get_diary_by_id, 
    update_diary, delete_diary, get_user_plants_for_diary, get_diary_stats
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/diary", tags=["diary"])


@router.post("/create", response_model=DiaryWriteResponse)
async def create_diary_endpoint(
    title: str = Form(...),
    content: str = Form(...),
    plant_nickname: Optional[str] = Form(None),
    plant_species: Optional[str] = Form(None),
    hashtag: Optional[str] = Form(None),
    weather: Optional[str] = Form(None),
    weather_icon: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    일기 작성
    
    - **title**: 일기 제목
    - **content**: 일기 내용
    - **plant_nickname**: 식물 별명 (선택)
    - **plant_species**: 식물 종류 (선택)
    - **hashtag**: 해시태그 (선택)
    - **weather**: 날씨 (선택)
    - **weather_icon**: 날씨 아이콘 (선택)
    - **image**: 일기 이미지 (선택)
    """
    try:
        # 요청 데이터 구성
        diary_request = DiaryWriteRequest(
            user_title=title,
            user_content=content,
            plant_nickname=plant_nickname,
            plant_species=plant_species,
            hashtag=hashtag
        )
        
        # 일기 생성
        diary = await create_diary(
            diary_request=diary_request,
            user_id=user["user_id"],
            image_file=image,
            weather=weather,
            weather_icon=weather_icon
        )
        
        return DiaryWriteResponse(
            idx=diary.idx,
            user_title=diary.user_title,
            user_content=diary.user_content,
            plant_nickname=diary.plant_nickname,
            plant_species=diary.plant_species,
            plant_reply=diary.plant_reply,
            weather=diary.weather,
            weather_icon=diary.weather_icon,
            img_url=diary.img_url,
            created_at=diary.created_at,
            updated_at=diary.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 작성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/list", response_model=List[DiaryOut])
async def get_diary_list(
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 목록 조회
    
    - **limit**: 조회할 일기 수 (기본값: 20)
    - **offset**: 건너뛸 일기 수 (기본값: 0)
    """
    try:
        diaries = await get_user_diaries(user["user_id"], limit, offset)
        return diaries
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{diary_id}", response_model=DiaryOut)
async def get_diary_detail(
    diary_id: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 일기 상세 조회
    
    - **diary_id**: 일기 ID
    """
    try:
        diary = await get_diary_by_id(diary_id, user["user_id"])
        if not diary:
            raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
        
        return diary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{diary_id}", response_model=DiaryWriteResponse)
async def update_diary_endpoint(
    diary_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    plant_nickname: Optional[str] = Form(None),
    plant_species: Optional[str] = Form(None),
    hashtag: Optional[str] = Form(None),
    weather: Optional[str] = Form(None),
    weather_icon: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    일기 수정
    
    - **diary_id**: 일기 ID
    - **title**: 일기 제목 (선택)
    - **content**: 일기 내용 (선택)
    - **plant_nickname**: 식물 별명 (선택)
    - **plant_species**: 식물 종류 (선택)
    - **hashtag**: 해시태그 (선택)
    - **weather**: 날씨 (선택)
    - **weather_icon**: 날씨 아이콘 (선택)
    - **image**: 일기 이미지 (선택)
    """
    try:
        # 요청 데이터 구성
        diary_request = DiaryUpdate(
            user_title=title,
            user_content=content,
            plant_nickname=plant_nickname,
            plant_species=plant_species,
            hashtag=hashtag,
            weather=weather,
            weather_icon=weather_icon
        )
        
        # 일기 수정
        diary = await update_diary(diary_id, diary_request, user["user_id"], image)
        if not diary:
            raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
        
        return DiaryWriteResponse(
            idx=diary.idx,
            user_title=diary.user_title,
            user_content=diary.user_content,
            plant_nickname=diary.plant_nickname,
            plant_species=diary.plant_species,
            plant_reply=diary.plant_reply,
            weather=diary.weather,
            weather_icon=diary.weather_icon,
            img_url=diary.img_url,
            created_at=diary.created_at,
            updated_at=diary.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{diary_id}")
async def delete_diary_endpoint(
    diary_id: int,
    user: dict = Depends(get_current_user)
):
    """
    일기 삭제
    
    - **diary_id**: 일기 ID
    """
    try:
        success = await delete_diary(diary_id, user["user_id"])
        if not success:
            raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
        
        return {"message": "일기가 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/plants/list")
async def get_user_plants_for_diary_endpoint(
    user: dict = Depends(get_current_user)
):
    """
    일기 작성용 사용자 식물 목록 조회
    """
    try:
        plants = await get_user_plants_for_diary(user["user_id"])
        return {"plants": plants}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats", response_model=DiaryStatsResponse)
async def get_diary_stats_endpoint(
    user: dict = Depends(get_current_user)
):
    """
    일기 통계 조회
    """
    try:
        stats = await get_diary_stats(user["user_id"])
        return DiaryStatsResponse(
            total_diaries=stats["total_diaries"],
            total_plants=0,  # TODO: 실제 식물 수 계산
            recent_diary_count=stats["recent_diaries"],
            most_active_plant=stats.get("most_active_plant_id"),
            average_diaries_per_plant=0.0  # TODO: 실제 평균 계산
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )
