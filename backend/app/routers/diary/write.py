from __future__ import annotations

import aiomysql
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel

from core.database import get_db
from crud import diary as diary_crud
from schemas.diary import DiaryWriteRequest, DiaryWriteResponse
from models.diary import Diary
from ml.plant_llm import plant_talk
from utils.weather_client import WeatherClient
from utils.errors import http_error
from utils.security import get_current_user
from services.image_service import save_uploaded_image

router = APIRouter(prefix="/diary", tags=["diary-write"])

# 날씨 클라이언트 인스턴스
weather_client = WeatherClient()

class DiaryCreateRequest(BaseModel):
    """일기 생성 요청"""
    user_title: str
    user_content: str
    plant_nickname: Optional[str] = None
    plant_species: Optional[str] = None
    hashtag: Optional[str] = None

class DiaryUpdateRequest(BaseModel):
    """일기 수정 요청"""
    user_title: Optional[str] = None
    user_content: Optional[str] = None
    plant_nickname: Optional[str] = None
    plant_species: Optional[str] = None
    hashtag: Optional[str] = None

@router.post("/create", response_model=DiaryWriteResponse)
async def create_diary(
    user_title: str = Form(...),
    user_content: str = Form(...),
    plant_nickname: Optional[str] = Form(None),
    plant_species: Optional[str] = Form(None),
    hashtag: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    새 일기 생성
    - 사진 업로드 지원
    - 날씨 자동 입력
    - 식물 답변 자동 생성
    """
    try:
        # 이미지 저장
        img_url = None
        if image:
            img_url = await save_uploaded_image(image, "diaries")
        
        # 날씨 정보 가져오기 (사용자 위치 기반, 현재는 더미)
        weather_data = await weather_client.get_weather("SEOUL_KR")
        weather = weather_data.get("condition")
        weather_icon = weather_data.get("icon_url")
        
        # 식물 답변 생성
        plant_reply = None
        if plant_species and user_content:
            # 습도 정보는 현재 더미값 (실제로는 센서 데이터에서 가져와야 함)
            moisture = 40.0  # 더미 습도값
            talk_result = await plant_talk(plant_species, user_content, moisture)
            plant_reply = talk_result.reply
        
        # 일기 생성
        diary = await diary_crud.create(
            db=db,
            user_id=user["user_id"],
            user_title=user_title,
            user_content=user_content,
            img_url=img_url,
            hashtag=hashtag,
            plant_nickname=plant_nickname,
            plant_species=plant_species,
            plant_reply=plant_reply,
            weather=weather,
            weather_icon=weather_icon,
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
            updated_at=diary.updated_at,
        )
        
    except Exception as e:
        raise http_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일기 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{diary_id}", response_model=DiaryWriteResponse)
async def update_diary(
    diary_id: int,
    user_title: Optional[str] = Form(None),
    user_content: Optional[str] = Form(None),
    plant_nickname: Optional[str] = Form(None),
    plant_species: Optional[str] = Form(None),
    hashtag: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    일기 수정
    - 기존 일기 조회 후 수정
    - 수정된 내용으로 식물 답변 재생성
    - 사진 교체 지원
    """
    try:
        # 기존 일기 조회
        existing_diary = await diary_crud.get_by_idx(db, diary_id)
        if not existing_diary:
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일기를 찾을 수 없습니다."
            )
        
        # 사용자 권한 확인
        if existing_diary.user_id != user["user_id"]:
            raise http_error(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 일기를 수정할 권한이 없습니다."
            )
        
        # 수정할 필드들 준비
        update_fields = {}
        
        if user_title is not None:
            update_fields["user_title"] = user_title
        if user_content is not None:
            update_fields["user_content"] = user_content
        if plant_nickname is not None:
            update_fields["plant_nickname"] = plant_nickname
        if plant_species is not None:
            update_fields["plant_species"] = plant_species
        if hashtag is not None:
            update_fields["hashtag"] = hashtag
        
        # 이미지 교체
        if image:
            img_url = await save_uploaded_image(image, "diaries")
            update_fields["img_url"] = img_url
        
        # 식물 답변 재생성 (내용이나 식물 종류가 변경된 경우)
        if (user_content is not None or plant_species is not None) and user_content:
            final_content = user_content if user_content is not None else existing_diary.user_content
            final_species = plant_species if plant_species is not None else existing_diary.plant_species
            
            if final_species:
                moisture = 40.0  # 더미 습도값
                talk_result = await plant_talk(final_species, final_content, moisture)
                update_fields["plant_reply"] = talk_result.reply
        
        # 날씨 정보 업데이트 (새로운 날씨로)
        weather_data = await weather_client.get_weather("SEOUL_KR")
        update_fields["weather"] = weather_data.get("condition")
        update_fields["weather_icon"] = weather_data.get("icon_url")
        
        # 일기 수정
        updated_diary = await diary_crud.patch(db, diary_id, **update_fields)
        
        return DiaryWriteResponse(
            idx=updated_diary.idx,
            user_title=updated_diary.user_title,
            user_content=updated_diary.user_content,
            plant_nickname=updated_diary.plant_nickname,
            plant_species=updated_diary.plant_species,
            plant_reply=updated_diary.plant_reply,
            weather=updated_diary.weather,
            weather_icon=updated_diary.weather_icon,
            img_url=updated_diary.img_url,
            created_at=updated_diary.created_at,
            updated_at=updated_diary.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일기 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{diary_id}", response_model=DiaryWriteResponse)
async def get_diary(
    diary_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    특정 일기 조회
    """
    try:
        diary = await diary_crud.get_by_idx(db, diary_id)
        if not diary:
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일기를 찾을 수 없습니다."
            )
        
        # 사용자 권한 확인
        if diary.user_id != user["user_id"]:
            raise http_error(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 일기를 조회할 권한이 없습니다."
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
            updated_at=diary.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일기 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{diary_id}")
async def delete_diary(
    diary_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    일기 삭제
    """
    try:
        # 기존 일기 조회
        existing_diary = await diary_crud.get_by_idx(db, diary_id)
        if not existing_diary:
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일기를 찾을 수 없습니다."
            )
        
        # 사용자 권한 확인
        if existing_diary.user_id != user["user_id"]:
            raise http_error(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 일기를 삭제할 권한이 없습니다."
            )
        
        # 일기 삭제
        deleted_count = await diary_crud.delete_by_idx(db, diary_id)
        
        if deleted_count == 0:
            raise http_error(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일기를 찾을 수 없습니다."
            )
        
        return {"message": "일기가 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise http_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일기 삭제 중 오류가 발생했습니다: {str(e)}"
        )
