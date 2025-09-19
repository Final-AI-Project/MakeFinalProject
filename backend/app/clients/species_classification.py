# backend/app/ml/species_classification.py
# 모델 서버(포트 5000)의 품종 분류 API를 호출하는 클라이언트

import httpx
import base64
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from core.config import settings

# 모델 서버 설정
MODEL_SERVER_URL = "http://10.151.212.165:5000"

class SpeciesClassificationResult(BaseModel):
    success: bool
    species: Optional[str] = None
    confidence: Optional[float] = None
    top_predictions: Optional[List[Dict[str, Any]]] = None
    message: str

async def classify_plant_species(image_data: bytes) -> SpeciesClassificationResult:
    """
    모델 서버의 품종 분류 API를 호출하여 식물 품종을 분류합니다.
    
    Args:
        image_data: 이미지 바이트 데이터
        
    Returns:
        SpeciesClassificationResult: 분류 결과
    """
    try:
        async with httpx.AsyncClient(timeout=settings.MODEL_SERVER_TIMEOUT) as client:
            # 이미지를 파일로 전송
            files = {
                'image': ('plant_image.jpg', image_data, 'image/jpeg')
            }
            
            response = await client.post(
                f"{MODEL_SERVER_URL}/species",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return SpeciesClassificationResult(
                        success=True,
                        species=data.get("species"),
                        confidence=data.get("confidence"),
                        top_predictions=data.get("top_predictions"),
                        message=data.get("message", "품종 분류가 완료되었습니다.")
                    )
                else:
                    # 모델 서버에서 에러가 발생한 경우
                    return SpeciesClassificationResult(
                        success=False,
                        message=data.get("message", "품종 분류에 실패했습니다.")
                    )
            else:
                # HTTP 에러가 발생한 경우
                return SpeciesClassificationResult(
                    success=False,
                    message=f"모델 서버 응답 오류: {response.status_code}"
                )
                
    except httpx.TimeoutException:
        return SpeciesClassificationResult(
            success=False,
            message="모델 서버 응답 시간 초과"
        )
    except httpx.ConnectError:
        return SpeciesClassificationResult(
            success=False,
            message="모델 서버에 연결할 수 없습니다"
        )
    except Exception as e:
        return SpeciesClassificationResult(
            success=False,
            message=f"품종 분류 중 오류가 발생했습니다: {str(e)}"
        )

async def classify_plant_species_from_url(image_url: str) -> SpeciesClassificationResult:
    """
    이미지 URL을 통해 품종 분류를 수행합니다.
    
    Args:
        image_url: 이미지 URL
        
    Returns:
        SpeciesClassificationResult: 분류 결과
    """
    try:
        async with httpx.AsyncClient(timeout=settings.MODEL_SERVER_TIMEOUT) as client:
            # 이미지 다운로드
            response = await client.get(image_url)
            if response.status_code == 200:
                image_data = response.content
                return await classify_plant_species(image_data)
            else:
                return SpeciesClassificationResult(
                    success=False,
                    message=f"이미지 다운로드 실패: {response.status_code}"
                )
    except Exception as e:
        return SpeciesClassificationResult(
            success=False,
            message=f"이미지 URL 처리 중 오류가 발생했습니다: {str(e)}"
        )

def get_species_korean_name(english_name: str) -> str:
    """
    영어 품종명을 한국어로 변환합니다.
    
    Args:
        english_name: 영어 품종명
        
    Returns:
        str: 한국어 품종명
    """
    # cascade 모델이 실제 학습한 품종들만 매핑 (models/main.py의 CLASSES 기준)
    species_mapping = {
        # 모델 서버의 CLASSES 배열에 정의된 품종들
        "monstera": "몬스테라",
        "stuckyi_sansevieria": "스투키",
        "zz_plant": "금전수",
        "cactus_succulent": "선인장/다육",
        "phalaenopsis": "호접란",
        "chamaedorea": "테이블야자",
        "schefflera": "홍콩야자",
        "spathiphyllum": "스파티필럼",
        "lady_palm": "관음죽",
        "ficus_audrey": "벵갈고무나무",
        "olive_tree": "올리브나무",
        "dieffenbachia": "디펜바키아",
        "boston_fern": "보스턴고사리"
    }
    
    return species_mapping.get(english_name, english_name)

def get_species_info(species_name: str) -> Dict[str, Any]:
    """
    품종명에 대한 추가 정보를 반환합니다.
    
    Args:
        species_name: 품종명
        
    Returns:
        Dict[str, Any]: 품종 정보
    """
    species_info = {
        "monstera": {
            "korean_name": "몬스테라",
            "care_level": "쉬움",
            "watering": "주 1-2회",
            "light": "중간 빛",
            "description": "큰 구멍이 뚫린 잎이 특징적인 인기 있는 관엽식물"
        },
        "stuckyi_sansevieria": {
            "korean_name": "스투키 산세베리아",
            "care_level": "매우 쉬움",
            "watering": "월 1-2회",
            "light": "낮은 빛",
            "description": "공기 정화 능력이 뛰어난 강건한 식물"
        },
        "zz_plant": {
            "korean_name": "ZZ플랜트",
            "care_level": "매우 쉬움",
            "watering": "월 1-2회",
            "light": "낮은 빛",
            "description": "물을 적게 주어도 잘 자라는 관리가 쉬운 식물"
        },
        "cactus_succulent": {
            "korean_name": "선인장/다육식물",
            "care_level": "쉬움",
            "watering": "월 1-2회",
            "light": "강한 빛",
            "description": "건조한 환경을 좋아하는 사막 식물"
        },
        "phalaenopsis": {
            "korean_name": "호접란",
            "care_level": "보통",
            "watering": "주 1회",
            "light": "중간 빛",
            "description": "아름다운 꽃을 피우는 인기 있는 난초"
        }
    }
    
    return species_info.get(species_name, {
        "korean_name": species_name,
        "care_level": "알 수 없음",
        "watering": "알 수 없음",
        "light": "알 수 없음",
        "description": "품종 정보를 찾을 수 없습니다."
    })
