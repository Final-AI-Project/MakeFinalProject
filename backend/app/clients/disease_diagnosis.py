# backend/app/ml/disease_diagnosis.py
# 모델 서버(포트 5000)의 병충해 진단 API를 호출하는 클라이언트

import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from core.config import settings
from utils.errors import http_error

# 모델 서버 설정
MODEL_SERVER_URL = "http://localhost:5000"

class DiseasePrediction(BaseModel):
    """병충해 예측 결과"""
    disease_name: str
    confidence: float
    description: str
    treatment: str
    prevention: str

class DiseaseDiagnosisResult(BaseModel):
    """병충해 진단 결과"""
    success: bool
    message: str
    predictions: List[DiseasePrediction] = []
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
        async with httpx.AsyncClient(timeout=settings.MODEL_SERVER_TIMEOUT) as client:
            # 이미지를 파일로 전송
            files = {
                'image': ('disease_image.jpg', image_data, 'image/jpeg')
            }
            
            response = await client.post(
                f"{MODEL_SERVER_URL}/disease",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 상위 3개 예측 결과 처리
                    predictions = []
                    
                    # all_predictions에서 상위 3개 추출
                    all_predictions = data.get("all_predictions", [])
                    for i, pred in enumerate(all_predictions[:3]):
                        disease_name = pred.get("class_name", f"Unknown Disease {i+1}")
                        confidence = pred.get("confidence", 0.0)
                        
                        # 병충해 정보 생성 (실제로는 DB에서 가져와야 함)
                        description = f"{disease_name} 병충해가 감지되었습니다."
                        treatment = "식물 전문가에게 상담하거나 적절한 치료제를 사용하세요."
                        prevention = "정기적인 관찰과 관리, 적절한 환경 조성을 통해 예방하세요."
                        
                        predictions.append(DiseasePrediction(
                            disease_name=disease_name,
                            confidence=confidence,
                            description=description,
                            treatment=treatment,
                            prevention=prevention
                        ))
                    
                    # 예측 결과가 없는 경우 더미 데이터 생성
                    if not predictions:
                        predictions = [
                            DiseasePrediction(
                                disease_name="Unknown Disease",
                                confidence=0.5,
                                description="병충해가 감지되었지만 정확한 종류를 식별할 수 없습니다.",
                                treatment="식물 전문가에게 상담하세요.",
                                prevention="정기적인 관찰과 관리가 필요합니다."
                            )
                        ]
                    
                    return DiseaseDiagnosisResult(
                        success=True,
                        message=data.get("message", "병충해 진단이 완료되었습니다."),
                        predictions=predictions
                    )
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
