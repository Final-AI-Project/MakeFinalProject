from __future__ import annotations

import httpx
from typing import Dict, Any, Optional
from fastapi import UploadFile
from core.config import get_settings

settings = get_settings()


class ModelClient:
    """AI 모델 서버와 통신하는 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.MODEL_SERVER_URL.rstrip('/')
        self.timeout = settings.MODEL_SERVER_TIMEOUT
    
    async def _make_request(
        self, 
        endpoint: str, 
        files: Optional[Dict[str, UploadFile]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """모델 서버에 HTTP 요청을 보내는 공통 메서드"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if files:
                    # 파일 업로드 요청
                    response = await client.post(url, files=files, data=data)
                else:
                    # 일반 요청
                    response = await client.post(url, json=data)
                
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException:
                raise Exception("모델 서버 응답 시간 초과")
            except httpx.HTTPStatusError as e:
                raise Exception(f"모델 서버 오류: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"모델 서버 연결 오류: {str(e)}")
    
    async def classify_species(self, image: UploadFile) -> Dict[str, Any]:
        """품종 분류 요청"""
        files = {"image": (image.filename, image.file, image.content_type)}
        return await self._make_request("/species", files=files)
    
    async def classify_health(self, image: UploadFile) -> Dict[str, Any]:
        """건강 상태 분류 요청"""
        files = {"image": (image.filename, image.file, image.content_type)}
        return await self._make_request("/health", files=files)
    
    async def classify_disease(self, image: UploadFile) -> Dict[str, Any]:
        """병충해/질병 분류 요청"""
        files = {"image": (image.filename, image.file, image.content_type)}
        return await self._make_request("/disease", files=files)
    
    async def health_check(self) -> Dict[str, Any]:
        """모델 서버 상태 확인"""
        return await self._make_request("/health")


# 전역 인스턴스
model_client = ModelClient()
