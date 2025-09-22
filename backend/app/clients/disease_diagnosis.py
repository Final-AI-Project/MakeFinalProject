# backend/app/ml/disease_diagnosis.py
# 모델 서버(포트 5000)의 병충해 진단 API를 호출하는 클라이언트

import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from core.config import settings
from utils.errors import http_error

# 모델 서버 설정
MODEL_SERVER_URL = settings.MODEL_SERVER_URL

class DiseasePrediction(BaseModel):
    """병충해 예측 결과"""
    class_name: str
    confidence: float
    rank: int

class DiseaseDiagnosisResult(BaseModel):
    """병충해 진단 결과"""
    success: bool
    health_check: bool
    health_status: str
    health_confidence: float
    message: str
    recommendation: str
    disease_predictions: List[DiseasePrediction] = []
    image_url: Optional[str] = None

async def diagnose_disease_from_image(image_data: bytes) -> DiseaseDiagnosisResult:
    """
    모델 서버의 병충해 진단 API를 호출하여 병충해를 진단합니다.
    
    Args:
        image_data: 이미지 바이트 데이터
        
    Returns:
        DiseaseDiagnosisResult: 진단 결과 (상위 3개 예측)
    """
    try:
        print(f"[DEBUG] 모델 서버 URL: {MODEL_SERVER_URL}")
        print(f"[DEBUG] 이미지 데이터 크기: {len(image_data)} bytes")
        
        async with httpx.AsyncClient(timeout=settings.MODEL_SERVER_TIMEOUT) as client:
            # 이미지를 파일로 전송
            files = {
                'image': ('disease_image.jpg', image_data, 'image/jpeg')
            }
            
            print(f"[DEBUG] 모델 서버에 요청 전송 중...")
            print(f"[DEBUG] 파일 정보: {files['image'][0]}, 크기: {len(files['image'][1])} bytes")
            
            response = await client.post(
                f"{MODEL_SERVER_URL}/disease",
                files=files
            )
            print(f"[DEBUG] 모델 서버 응답 상태: {response.status_code}")
            print(f"[DEBUG] 모델 서버 응답 내용: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 새로운 응답 구조에 맞게 처리
                    disease_predictions = []
                    
                    # disease_predictions에서 데이터 추출
                    for pred in data.get("disease_predictions", []):
                        disease_predictions.append(DiseasePrediction(
                            class_name=pred.get("class_name", "Unknown Disease"),
                            confidence=pred.get("confidence", 0.0),
                            rank=pred.get("rank", 1)
                        ))
                    
                    result = DiseaseDiagnosisResult(
                        success=True,
                        health_check=data.get("health_check", False),
                        health_status=data.get("health_status", "unknown"),
                        health_confidence=data.get("health_confidence", 0.0),
                        message=data.get("message", "진단이 완료되었습니다."),
                        recommendation=data.get("recommendation", "정기적인 관찰을 계속하세요."),
                        disease_predictions=disease_predictions
                    )
                    print(f"[DEBUG] 최종 결과: {result}")
                    return result
                else:
                    raise http_error(
                        "disease_diagnosis_failed",
                        data.get("message", "모델 서버에서 병충해 진단에 실패했습니다."),
                        status=400
                    )
            else:
                raise http_error(
                    "model_server_error",
                    f"모델 서버 오류: {response.status_code} - {response.text}",
                    status=500
                )
                
    except httpx.ConnectError:
        # 모델 서버 연결 실패 시 더미 데이터 반환
        return _get_dummy_diagnosis_result()
    except Exception as e:
        raise http_error(
            "disease_diagnosis_exception",
            f"병충해 진단 중 예외 발생: {str(e)}",
            status=500
        )

def _get_dummy_diagnosis_result() -> DiseaseDiagnosisResult:
    """모델 서버 연결 실패 시 더미 진단 결과 반환"""
    dummy_predictions = [
        DiseasePrediction(
            disease_name="Leaf Spot",
            confidence=0.85,
            description="잎에 갈색 반점이 나타나는 병충해입니다. 주로 과습이나 통풍 부족으로 발생합니다.",
            treatment="감염된 잎을 제거하고, 적절한 살균제를 사용하세요. 통풍을 개선하고 물주기를 조절하세요.",
            prevention="적절한 간격을 유지하고, 잎에 물이 닿지 않도록 물주기하세요."
        ),
        DiseasePrediction(
            disease_name="Powdery Mildew",
            confidence=0.72,
            description="잎 표면에 흰색 가루 같은 곰팡이가 생기는 병충해입니다.",
            treatment="감염된 부분을 제거하고, 유황 기반 살균제를 사용하세요.",
            prevention="습도를 낮추고, 충분한 햇빛과 통풍을 확보하세요."
        ),
        DiseasePrediction(
            disease_name="Aphid Infestation",
            confidence=0.68,
            description="진딧물이 식물에 기생하여 영양분을 빼앗는 해충입니다.",
            treatment="천연 살충제나 비누수를 사용하여 제거하세요.",
            prevention="정기적인 관찰과 천적 곤충 유입을 통해 예방하세요."
        )
    ]
    
    return DiseaseDiagnosisResult(
        success=True,
        message="모델 서버 연결 실패로 더미 데이터를 반환합니다.",
        predictions=dummy_predictions
    )
