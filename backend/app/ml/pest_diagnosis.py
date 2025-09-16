from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import UploadFile
from .model_client import model_client
from utils.errors import http_error


class PestDiagnosisService:
    """병충해 진단 서비스"""
    
    async def diagnose_pest(self, image: UploadFile) -> Dict[str, Any]:
        """
        식물의 병충해를 진단합니다.
        
        Args:
            image: 진단할 식물 이미지
            
        Returns:
            진단 결과 딕셔너리
        """
        try:
            # 이미지 파일 검증
            if not image.filename:
                raise http_error("invalid_file", "파일명이 없습니다.", 400)
            
            if not image.content_type or not image.content_type.startswith('image/'):
                raise http_error("invalid_file_type", "이미지 파일만 업로드 가능합니다.", 400)
            
            # 모델 서버에 요청
            result = await model_client.classify_disease(image)
            
            # 결과 검증
            if not result.get('success', False):
                raise http_error("diagnosis_failed", "병충해 진단에 실패했습니다.", 500)
            
            return {
                "success": True,
                "disease": result.get('disease', 'unknown'),
                "confidence": result.get('confidence', 0.0),
                "disease_info": result.get('disease_info', {}),
                "recommendation": result.get('recommendation', '식물 상태를 주의 깊게 관찰하세요.'),
                "all_predictions": result.get('all_predictions', []),
                "message": result.get('message', '병충해 진단이 완료되었습니다.')
            }
            
        except Exception as e:
            if hasattr(e, 'status_code'):
                raise e
            raise http_error("diagnosis_error", f"병충해 진단 중 오류가 발생했습니다: {str(e)}", 500)


# 전역 인스턴스
pest_service = PestDiagnosisService()
