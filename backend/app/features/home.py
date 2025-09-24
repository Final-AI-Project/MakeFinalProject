from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from services.auth_service import get_current_user
from repositories.dashboard import get_user_plants_with_status
from schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/home", tags=["home"])

@router.get("/plants/current", response_model=DashboardResponse)
async def get_current_plants_status(
    user: dict = Depends(get_current_user)
):
    """
    메인페이지에서 사용할 현재 식물들의 상태 정보를 조회합니다.
    습도 정보, 품종별 최적 습도 범위, 상태 정보를 포함합니다.
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="사용자 인증 정보가 없습니다."
            )
        
        # 대시보드 데이터 조회 (품종별 습도 범위 포함)
        result = await get_user_plants_with_status(user_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 상태 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )
