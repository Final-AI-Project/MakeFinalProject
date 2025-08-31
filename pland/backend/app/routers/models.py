"""
Models Router
모델 관리 API
"""

import os
import glob
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class ModelInfo(BaseModel):
    """모델 정보"""
    name: str
    path: str
    size_mb: float
    created_at: str
    model_type: str  # pytorch, onnx
    is_active: bool


class ModelSelectionRequest(BaseModel):
    """모델 선택 요청"""
    model_name: str


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """
    사용 가능한 모델 목록 조회
    
    Returns:
        모델 목록 및 현재 활성 모델
    """
    try:
        models_dir = settings.model_cache_dir
        if not os.path.exists(models_dir):
            return {
                "models": [],
                "active_model": None,
                "total_count": 0
            }
        
        models = []
        
        # PyTorch 모델 (.pt, .pth)
        pt_models = glob.glob(os.path.join(models_dir, "*.pt")) + glob.glob(os.path.join(models_dir, "*.pth"))
        for model_path in pt_models:
            model_name = os.path.basename(model_path)
            model_info = await get_model_info(model_path, "pytorch")
            models.append(model_info)
        
        # ONNX 모델 (.onnx)
        onnx_models = glob.glob(os.path.join(models_dir, "*.onnx"))
        for model_path in onnx_models:
            model_name = os.path.basename(model_path)
            model_info = await get_model_info(model_path, "onnx")
            models.append(model_info)
        
        # 현재 활성 모델 확인
        active_model = None
        for model in models:
            if model.is_active:
                active_model = model.name
                break
        
        return {
            "models": [model.dict() for model in models],
            "active_model": active_model,
            "total_count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"모델 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


async def get_model_info(model_path: str, model_type: str) -> ModelInfo:
    """모델 정보 조회"""
    import time
    
    stat = os.stat(model_path)
    size_mb = stat.st_size / (1024 * 1024)  # Convert to MB
    created_at = time.ctime(stat.st_ctime)
    
    # 활성 모델 확인 (임시로 기본 모델명으로 판단)
    is_active = os.path.basename(model_path) == f"{settings.default_model_name}.pt"
    
    return ModelInfo(
        name=os.path.basename(model_path),
        path=model_path,
        size_mb=round(size_mb, 2),
        created_at=created_at,
        model_type=model_type,
        is_active=is_active
    )


@router.post("/models/select")
async def select_model(request: ModelSelectionRequest) -> Dict[str, Any]:
    """
    서빙 모델 변경
    
    Args:
        request: 모델 선택 요청
    
    Returns:
        모델 선택 결과
    """
    try:
        model_name = request.model_name
        model_path = os.path.join(settings.model_cache_dir, model_name)
        
        # 모델 파일 존재 확인
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404,
                detail=f"모델 파일을 찾을 수 없습니다: {model_name}"
            )
        
        # 모델 파일 확장자 확인
        if not model_name.endswith(('.pt', '.pth', '.onnx')):
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 모델 형식입니다. (.pt, .pth, .onnx만 지원)"
            )
        
        # 모델 로드 테스트 (간단한 검증)
        try:
            if model_name.endswith('.onnx'):
                import onnxruntime as ort
                ort.InferenceSession(model_path)
            else:
                import torch
                torch.load(model_path, map_location='cpu')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"모델 파일이 손상되었거나 로드할 수 없습니다: {str(e)}"
            )
        
        # TODO: 실제로는 설정 파일이나 데이터베이스에 활성 모델 정보 저장
        # 현재는 임시로 성공 응답만 반환
        
        return {
            "status": "success",
            "message": f"모델이 성공적으로 변경되었습니다: {model_name}",
            "selected_model": model_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"모델 선택 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/models/{model_name}")
async def delete_model(model_name: str) -> Dict[str, Any]:
    """
    모델 삭제
    
    Args:
        model_name: 삭제할 모델명
    
    Returns:
        삭제 결과
    """
    try:
        model_path = os.path.join(settings.model_cache_dir, model_name)
        
        # 모델 파일 존재 확인
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404,
                detail=f"모델 파일을 찾을 수 없습니다: {model_name}"
            )
        
        # 활성 모델 삭제 방지
        if model_name == f"{settings.default_model_name}.pt":
            raise HTTPException(
                status_code=400,
                detail="기본 모델은 삭제할 수 없습니다."
            )
        
        # 파일 삭제
        os.remove(model_path)
        
        return {
            "status": "success",
            "message": f"모델이 성공적으로 삭제되었습니다: {model_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"모델 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/models/info/{model_name}")
async def get_model_details(model_name: str) -> Dict[str, Any]:
    """
    모델 상세 정보 조회
    
    Args:
        model_name: 모델명
    
    Returns:
        모델 상세 정보
    """
    try:
        model_path = os.path.join(settings.model_cache_dir, model_name)
        
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404,
                detail=f"모델 파일을 찾을 수 없습니다: {model_name}"
            )
        
        # 기본 정보
        model_info = await get_model_info(model_path, "unknown")
        
        # 추가 정보 (모델 타입별)
        additional_info = {}
        
        if model_name.endswith('.onnx'):
            try:
                import onnx
                onnx_model = onnx.load(model_path)
                additional_info = {
                    "input_shape": [input.shape for input in onnx_model.graph.input],
                    "output_shape": [output.shape for output in onnx_model.graph.output],
                    "opset_version": onnx_model.opset_import[0].version
                }
            except Exception:
                additional_info = {"error": "ONNX 모델 정보를 읽을 수 없습니다."}
        
        elif model_name.endswith(('.pt', '.pth')):
            try:
                import torch
                checkpoint = torch.load(model_path, map_location='cpu')
                additional_info = {
                    "model_keys": list(checkpoint.keys()) if isinstance(checkpoint, dict) else "Not a dict",
                    "state_dict_keys": list(checkpoint['state_dict'].keys()) if isinstance(checkpoint, dict) and 'state_dict' in checkpoint else None
                }
            except Exception:
                additional_info = {"error": "PyTorch 모델 정보를 읽을 수 없습니다."}
        
        return {
            **model_info.dict(),
            "additional_info": additional_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"모델 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )
