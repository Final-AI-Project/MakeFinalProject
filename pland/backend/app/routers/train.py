"""
Training Router
모델 학습 API
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import settings
from app.ml.train_classifier import ModelTrainer

router = APIRouter()

# 전역 변수로 학습 상태 관리
training_status = {
    "is_training": False,
    "current_epoch": 0,
    "total_epochs": 0,
    "current_loss": 0.0,
    "current_accuracy": 0.0,
    "start_time": None,
    "end_time": None,
    "error": None
}


class TrainingRequest(BaseModel):
    """학습 요청 모델"""
    dataset_source: str = "samples"  # samples, local, plantvillage
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    freeze_backbone: bool = False
    output_name: str = "plant_whisperer_model"
    validation_split: float = 0.2
    random_seed: int = 42


class TrainingResponse(BaseModel):
    """학습 응답 모델"""
    status: str
    message: str
    task_id: Optional[str] = None
    estimated_time: Optional[int] = None


async def run_training_task(request: TrainingRequest):
    """백그라운드에서 학습 실행"""
    global training_status
    
    try:
        training_status.update({
            "is_training": True,
            "current_epoch": 0,
            "total_epochs": request.epochs,
            "current_loss": 0.0,
            "current_accuracy": 0.0,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "error": None
        })
        
        # 학습기 초기화
        trainer = ModelTrainer(
            dataset_source=request.dataset_source,
            epochs=request.epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            freeze_backbone=request.freeze_backbone,
            output_name=request.output_name,
            validation_split=request.validation_split,
            random_seed=request.random_seed
        )
        
        # 학습 실행
        await trainer.train(
            progress_callback=lambda epoch, loss, accuracy: update_training_progress(epoch, loss, accuracy)
        )
        
        training_status.update({
            "is_training": False,
            "end_time": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        training_status.update({
            "is_training": False,
            "error": str(e),
            "end_time": datetime.utcnow().isoformat()
        })
        raise


def update_training_progress(epoch: int, loss: float, accuracy: float):
    """학습 진행상황 업데이트"""
    global training_status
    training_status.update({
        "current_epoch": epoch,
        "current_loss": loss,
        "current_accuracy": accuracy
    })


@router.post("/train", response_model=TrainingResponse)
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
) -> TrainingResponse:
    """
    모델 학습 시작
    
    Args:
        request: 학습 요청 파라미터
        background_tasks: 백그라운드 작업 관리
    
    Returns:
        학습 시작 응답
    """
    global training_status
    
    # 이미 학습 중인지 확인
    if training_status["is_training"]:
        raise HTTPException(
            status_code=409,
            detail="이미 학습이 진행 중입니다. 현재 학습이 완료될 때까지 기다려주세요."
        )
    
    # 요청 파라미터 검증
    if request.epochs <= 0 or request.epochs > 100:
        raise HTTPException(
            status_code=400,
            detail="에포크 수는 1-100 사이여야 합니다."
        )
    
    if request.batch_size <= 0 or request.batch_size > 128:
        raise HTTPException(
            status_code=400,
            detail="배치 크기는 1-128 사이여야 합니다."
        )
    
    if request.learning_rate <= 0 or request.learning_rate > 1.0:
        raise HTTPException(
            status_code=400,
            detail="학습률은 0-1 사이여야 합니다."
        )
    
    # 백그라운드에서 학습 시작
    background_tasks.add_task(run_training_task, request)
    
    # 예상 소요 시간 계산 (대략적)
    estimated_minutes = request.epochs * 2  # 에포크당 약 2분 가정
    
    return TrainingResponse(
        status="started",
        message="학습이 시작되었습니다. /api/train/status에서 진행상황을 확인할 수 있습니다.",
        task_id="training_task",
        estimated_time=estimated_minutes
    )


@router.get("/train/status")
async def get_training_status() -> Dict[str, Any]:
    """
    학습 상태 확인
    
    Returns:
        현재 학습 상태
    """
    global training_status
    
    # 진행률 계산
    progress = 0.0
    if training_status["total_epochs"] > 0:
        progress = (training_status["current_epoch"] / training_status["total_epochs"]) * 100
    
    return {
        "is_training": training_status["is_training"],
        "progress": round(progress, 2),
        "current_epoch": training_status["current_epoch"],
        "total_epochs": training_status["total_epochs"],
        "current_loss": training_status["current_loss"],
        "current_accuracy": training_status["current_accuracy"],
        "start_time": training_status["start_time"],
        "end_time": training_status["end_time"],
        "error": training_status["error"]
    }


@router.post("/train/stop")
async def stop_training() -> Dict[str, Any]:
    """
    학습 중단 (향후 구현)
    """
    raise HTTPException(
        status_code=501,
        detail="학습 중단 기능은 아직 구현되지 않았습니다."
    )


@router.get("/train/history")
async def get_training_history() -> Dict[str, Any]:
    """
    학습 히스토리 조회 (향후 구현)
    """
    raise HTTPException(
        status_code=501,
        detail="학습 히스토리 기능은 아직 구현되지 않았습니다."
    )
