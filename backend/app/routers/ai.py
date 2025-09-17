from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Dict, Any
from ml.species_classification import species_service
from ml.pest_diagnosis import pest_service
from ml.health_classification import health_service
from ml.model_client import model_client
from utils.security import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/species")
async def classify_species(
    image: UploadFile = File(..., description="분류할 식물 이미지"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    식물 품종을 분류합니다.
    """
    return await species_service.classify_species(image)


@router.post("/health")
async def classify_health(
    image: UploadFile = File(..., description="분류할 식물 이미지"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    식물의 건강 상태를 분류합니다.
    """
    return await health_service.classify_health(image)


@router.post("/disease")
async def diagnose_disease(
    image: UploadFile = File(..., description="진단할 식물 이미지"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    식물의 병충해/질병을 진단합니다.
    """
    return await pest_service.diagnose_pest(image)


@router.get("/status")
async def get_ai_status(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    AI 모델 서버 상태를 확인합니다.
    """
    try:
        status = await model_client.health_check()
        return {
            "success": True,
            "model_server_status": "connected",
            "models": status.get("models", {}),
            "device": status.get("device", "unknown"),
            "api_endpoints": status.get("api_endpoints", [])
        }
    except Exception as e:
        return {
            "success": False,
            "model_server_status": "disconnected",
            "error": str(e)
        }
