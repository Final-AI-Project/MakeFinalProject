"""
Inference Router
식물 이미지 분석 API
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.preprocess import ImagePreprocessor
from app.services.classifier import PlantClassifier
from app.services.plant_speech import PlantSpeechGenerator
from app.utils.io_utils import save_uploaded_file, validate_image_file

router = APIRouter()


@router.post("/predict")
async def predict_plant(
    file: UploadFile = File(...),
    use_onnx: bool = Form(False),
    confidence_threshold: float = Form(0.5)
) -> Dict[str, Any]:
    """
    식물 이미지 분석
    
    Args:
        file: 업로드된 이미지 파일
        use_onnx: ONNX 런타임 사용 여부
        confidence_threshold: 신뢰도 임계값
    
    Returns:
        분석 결과 (품종, 질병, 식물의 말)
    """
    try:
        # 파일 검증
        if not file:
            raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다.")
        
        # 파일 확장자 검증
        if not validate_image_file(file, settings.upload_allowed_extensions):
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(settings.upload_allowed_extensions)}"
            )
        
        # 파일 크기 검증
        if file.size > settings.upload_max_size:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.upload_max_size // 1024 // 1024}MB"
            )
        
        # 고유 파일명 생성
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_extension}"
        
        # 파일 저장
        file_path = await save_uploaded_file(file, filename, settings.storage_path)
        
        # 이미지 전처리
        preprocessor = ImagePreprocessor()
        processed_image, mask_path, crop_info = await preprocessor.preprocess_image(file_path)
        
        # 분류기 초기화 및 추론
        classifier = PlantClassifier(
            model_name=settings.default_model_name,
            device=settings.inference_device,
            use_onnx=use_onnx
        )
        
        # 품종 및 질병 분류
        species_results = await classifier.classify_species(processed_image)
        disease_results = await classifier.classify_disease(processed_image)
        
        # 식물의 말 생성
        speech_generator = PlantSpeechGenerator()
        plant_speech = speech_generator.generate_speech(
            species_results=species_results,
            disease_results=disease_results,
            confidence_threshold=confidence_threshold
        )
        
        # 결과 정리
        result = {
            "species_topk": species_results[:5],  # Top 5 품종
            "disease_topk": disease_results[:5],  # Top 5 질병
            "confidence": {
                "species": species_results[0]["confidence"] if species_results else 0.0,
                "disease": disease_results[0]["confidence"] if disease_results else 0.0
            },
            "talk": plant_speech,
            "debug": {
                "file_id": file_id,
                "original_filename": file.filename,
                "processed_image_size": processed_image.shape if processed_image is not None else None,
                "mask_path": mask_path,
                "crop_info": crop_info,
                "inference_time": datetime.utcnow().isoformat()
            }
        }
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        # 로그 기록
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail="이미지 분석 중 오류가 발생했습니다."
        )


@router.post("/predict/batch")
async def predict_batch(
    files: List[UploadFile] = File(...),
    use_onnx: bool = Form(False),
    confidence_threshold: float = Form(0.5)
) -> Dict[str, Any]:
    """
    배치 이미지 분석 (향후 구현)
    """
    raise HTTPException(
        status_code=501,
        detail="배치 처리 기능은 아직 구현되지 않았습니다."
    )
