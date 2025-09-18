from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from schemas.diary import (
    DiaryListResponse,
    DiarySearchRequest,
    DiaryStatsResponse,
    DiaryListItemResponse
)
from crud.diary_list import (
    get_user_diary_list,
    search_user_diaries,
    get_diary_stats,
    get_plant_diary_summary,
    get_recent_diaries
)
from utils.security import get_current_user

router = APIRouter(prefix="/diary-list", tags=["diary-list"])

@router.get("", response_model=DiaryListResponse)
async def get_diary_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    order_by: str = Query("created_at", description="정렬 기준 (created_at, updated_at, plant_nickname, plant_species, user_title)"),
    order_direction: str = Query("desc", description="정렬 방향 (asc, desc)"),
    plant_nickname: Optional[str] = Query(None, description="식물 별명으로 필터링"),
    plant_species: Optional[str] = Query(None, description="식물 종류로 필터링"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    hashtag: Optional[str] = Query(None, description="해시태그로 필터링"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **order_by**: 정렬 기준 (created_at, updated_at, plant_nickname, plant_species, user_title)
    - **order_direction**: 정렬 방향 (asc, desc)
    - **plant_nickname**: 식물 별명으로 필터링
    - **plant_species**: 식물 종류로 필터링
    - **start_date**: 시작 날짜 (YYYY-MM-DD 형식)
    - **end_date**: 종료 날짜 (YYYY-MM-DD 형식)
    - **hashtag**: 해시태그로 필터링
    """
    try:
        # 날짜 파싱
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date:
            try:
                from datetime import datetime
                start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="시작 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                )
        
        if end_date:
            try:
                from datetime import datetime
                end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="종료 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                )
        
        # 검색 요청 구성
        search_request = DiarySearchRequest(
            plant_nickname=plant_nickname,
            plant_species=plant_species,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            hashtag=hashtag
        )
        
        result = await get_user_diary_list(
            user_id=user["user_id"],
            page=page,
            limit=limit,
            order_by=order_by,
            order_direction=order_direction,
            search_request=search_request
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search", response_model=DiaryListResponse)
async def search_diaries(
    q: str = Query(..., min_length=1, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: dict = Depends(get_current_user)
):
    """
    일기 내용을 검색합니다.
    
    - **q**: 검색어 (필수) - 제목과 내용에서 검색
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    try:
        result = await search_user_diaries(
            user_id=user["user_id"],
            query=q,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats", response_model=DiaryStatsResponse)
async def get_diary_statistics(
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 통계 정보를 조회합니다.
    
    - 전체 일기 수
    - 전체 식물 수
    - 최근 7일 일기 수
    - 가장 활발한 식물
    - 식물당 평균 일기 수
    """
    try:
        result = await get_diary_stats(user["user_id"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/summary")
async def get_plant_diary_summary_endpoint(
    user: dict = Depends(get_current_user)
):
    """
    식물별 일기 요약을 조회합니다.
    
    - 각 식물별 일기 수
    - 마지막 일기 작성일
    - 첫 일기 작성일
    """
    try:
        result = await get_plant_diary_summary(user["user_id"])
        return {
            "user_id": user["user_id"],
            "plant_summaries": result,
            "total_plants": len(result)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물별 일기 요약 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/recent", response_model=List[DiaryListItemResponse])
async def get_recent_diaries_endpoint(
    limit: int = Query(5, ge=1, le=20, description="조회할 일기 수"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 최근 일기를 조회합니다.
    
    - **limit**: 조회할 일기 수 (기본값: 5, 최대: 20)
    """
    try:
        result = await get_recent_diaries(user["user_id"], limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최근 일기 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/export")
async def export_diaries(
    format: str = Query("json", description="내보내기 형식 (json, csv)"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    user: dict = Depends(get_current_user)
):
    """
    일기를 내보냅니다.
    
    - **format**: 내보내기 형식 (json, csv)
    - **start_date**: 시작 날짜 (선택사항)
    - **end_date**: 종료 날짜 (선택사항)
    """
    try:
        # 날짜 파싱
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date:
            try:
                from datetime import datetime
                start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="시작 날짜 형식이 올바르지 않습니다."
                )
        
        if end_date:
            try:
                from datetime import datetime
                end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="종료 날짜 형식이 올바르지 않습니다."
                )
        
        # 검색 요청 구성
        search_request = DiarySearchRequest(
            start_date=start_date_parsed,
            end_date=end_date_parsed
        )
        
        # 모든 일기 조회 (페이지네이션 없이)
        result = await get_user_diary_list(
            user_id=user["user_id"],
            page=1,
            limit=10000,  # 큰 수로 설정하여 모든 일기 조회
            search_request=search_request
        )
        
        if format.lower() == "csv":
            # CSV 형식으로 변환
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 헤더 작성
            writer.writerow([
                "제목", "내용", "식물별명", "식물종류", "날씨", "해시태그", 
                "작성일", "수정일"
            ])
            
            # 데이터 작성
            for diary in result.diaries:
                writer.writerow([
                    diary.user_title,
                    diary.user_content,
                    diary.plant_nickname or "",
                    diary.plant_species or "",
                    diary.weather or "",
                    diary.hashtag or "",
                    diary.created_at.strftime("%Y-%m-%d %H:%M:%S") if diary.created_at else "",
                    diary.updated_at.strftime("%Y-%m-%d %H:%M:%S") if diary.updated_at else ""
                ])
            
            return {
                "format": "csv",
                "data": output.getvalue(),
                "filename": f"diaries_{user['user_id']}_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        else:
            # JSON 형식
            return {
                "format": "json",
                "data": [diary.dict() for diary in result.diaries],
                "total_count": result.total_count,
                "exported_at": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 내보내기 중 오류가 발생했습니다: {str(e)}"
        )
