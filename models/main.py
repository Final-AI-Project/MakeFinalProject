# ------ 모듈 임포트
import os
import json
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
from ultralytics import YOLO

# === PyTorch 2.6 호환성을 위한 설정 ===
# torch.load의 weights_only를 False로 설정
torch.serialization.DEFAULT_PROTOCOL = 2

# 전역적으로 torch.load 설정
original_torch_load = torch.load
def safe_torch_load(*args, **kwargs):
    # weights_only가 이미 있으면 제거하고 False로 설정
    kwargs.pop('weights_only', None)
    kwargs['weights_only'] = False
    return original_torch_load(*args, **kwargs)
torch.load = safe_torch_load
from detector.leaf_segmentation import LeafSegmentationModel
from classifier.cascade.plant_classifier import get_plant_service, predict_plant_species
from classifier.pestcase.plant_classifier import predict_image as predict_pest

# 품종 분류 클래스 정의 (cascade 폴더의 labels.txt와 동일한 순서)
CLASSES = [
    "보스턴고사리", "선인장", "관음죽", "디펜바키아", "벵갈고무나무",
    "테이블야자", "몬스테라", "올리브나무", "호접란", "홍콩야자",
    "스파티필럼", "스투키", "금전수"
]
from healthy.healthy import predict_image as predict_health

# humidity.py 임포트
from humidity.humidity import META, PredictResp, PredictReq, S_REF_DEFAULT, S_DRY, hours_until_threshold, apply_eta_calibration


# ------ FastAPI 앱
app = FastAPI()

# ------ CORS - 모든 오리진 허용
origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "*"  # 모든 오리진 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ----------------- 모델 경로 설정
SEG_MODEL_PATH = "weight/seg_best.pt"
SPECIES_MODEL_PATH = "classifier/cascade/weight/efficientnet_b0_best.pth"  # 품종 분류 모델
HEALTH_MODEL_PATH = "healthy/healthy.pt"    # 건강 상태 모델
PEST_MODEL_PATH = "classifier/pestcase/pestcase_best.pt"  # 병충해 분류 모델
HUMID_MODEL_PATH = "humidity/model.joblib" # 급수 코치 모델

# -------------------- 디바이스 결정 --------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Device: {device}")

# -------------------- 모델 로딩 --------------------
print("🔧 Loading Leaf Segmentation Model...")
print("⚠️ 세그멘테이션 모델 사용 중지됨 (호환성 문제)")
seg_model = None

# 품종 분류 모델 로드 (새로운 구조)
print("🔧 Loading Species Classification Model...")
try:
    species_service = get_plant_service()
    print(f"[DEBUG] species_service 타입: {type(species_service)}")
    print(f"[DEBUG] species_service.model: {species_service.model}")
    
    if species_service.model is not None:
        print("✅ 품종 분류 모델 로드 완료")
        species_model = species_service  # 서비스 객체를 모델로 사용
        print(f"[DEBUG] species_model 설정 완료: {type(species_model)}")
    else:
        print("⚠️ 품종 분류 모델 로드 실패 - model이 None")
        species_model = None
except Exception as e:
    print(f"❌ 품종 분류 모델 로드 실패: {e}")
    import traceback
    print(f"[DEBUG] 트레이스백: {traceback.format_exc()}")
    species_model = None

# 건강 상태 모델 로드
print("🔧 Loading Health Classification Model...")
try:
    health_model = YOLO(HEALTH_MODEL_PATH) if os.path.exists(HEALTH_MODEL_PATH) else None
    if health_model:
        print("✅ 건강 상태 모델 로드 완료")
    else:
        print("⚠️ 건강 상태 모델 파일이 없습니다.")
except Exception as e:
    print(f"❌ 건강 상태 모델 로드 실패: {e}")
    health_model = None

# 병충해 분류 모델 로드
print("🔧 Loading Pest Classification Model...")
try:
    if os.path.exists(PEST_MODEL_PATH):
        # 병충해 모델은 predict_image 함수를 통해 지연 로딩됨
        print("✅ 병충해 분류 모델 로드 완료")
        pest_model = True  # 모델이 사용 가능함을 표시
    else:
        print("⚠️ 병충해 분류 모델 파일이 없습니다.")
        pest_model = None
except Exception as e:
    print(f"❌ 병충해 분류 모델 로드 실패: {e}")
    pest_model = None

# -------------------------- 잎 탐지 및 세그멘테이션 API (비활성화됨)
@app.post("/detector")
async def detect_and_segment_leaves(
    image: UploadFile = File(...)
):
    """
    이미지에서 식물의 잎을 탐지하고 세그멘테이션하여 크롭된 잎 이미지들을 반환
    (현재 호환성 문제로 비활성화됨)
    """
    return JSONResponse(content={
        'success': False,
        'message': '세그멘테이션 모델이 호환성 문제로 현재 비활성화되어 있습니다.',
        'error': 'segmentation_model_disabled',
        'note': '모델 파일은 보존되어 있으며, 호환성 문제 해결 후 재활성화 예정입니다.'
    })

# -------------------------- 품종 분류기 API
@app.post("/species")
async def classify_species(
    image: UploadFile = File(...)
):
    """
    식물의 품종을 분류
    """
    try:
        # 업로드된 이미지 읽기
        image_data = await image.read()
        
        # 새로운 모델로 예측 수행
        result = predict_plant_species(image_data)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "분류 중 오류가 발생했습니다."))
        
        predictions = result["predictions"]
        top_prediction = result["top_prediction"]
        
        return JSONResponse(content={
            'success': True,
            'message': f"품종 분류 완료: {top_prediction['class_name']}",
            'species': top_prediction['class_name'],
            'confidence': round(top_prediction['confidence'], 4),
            'top_predictions': [
                {
                    'class_name': pred['class_name'],
                    'confidence': round(pred['confidence'], 4)
                }
                for pred in predictions
            ]
        })
        
    except Exception as e:
        print(f"❌ 품종 분류 오류: {e}")
        raise HTTPException(status_code=500, detail=f"품종 분류 중 오류가 발생했습니다: {str(e)}")

# -------------------------- 잎 상태 분류기 API
@app.post("/health")
async def classify_health(
    image: UploadFile = File(...)
):
    """
    잎의 건강 상태를 분류
    """
    if health_model is None:
        raise HTTPException(status_code=500, detail="건강 상태 분류 모델이 로드되지 않았습니다.")
    
    try:
        # 업로드된 이미지 읽기
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # 건강 상태 예측 수행
        result = predict_health(pil_image, topk=3)
        
        # 결과 포맷팅
        health_status = result['class_name']
        confidence = result['score']
        
        # 건강 상태에 따른 메시지 생성
        status_messages = {
            'healthy': '식물이 건강한 상태입니다.',
            'unhealthy': '식물에 문제가 있을 수 있습니다.',
            'diseased': '식물에 질병이 있을 수 있습니다.'
        }
        
        message = status_messages.get(health_status, f"건강 상태: {health_status}")
        
        return JSONResponse(content={
            'success': True,
            'message': message,
            'health_status': health_status,
            'confidence': round(confidence, 4),
            'recommendation': get_health_recommendation(health_status)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"건강 상태 분류 중 오류가 발생했습니다: {str(e)}")

def get_health_recommendation(health_status: str) -> str:
    """건강 상태에 따른 권장사항 반환"""
    recommendations = {
        'healthy': '현재 상태를 유지하세요. 정기적인 물주기와 햇빛을 제공하세요.',
        'unhealthy': '식물의 환경을 점검해보세요. 물주기, 햇빛, 온도를 확인하세요.',
        'diseased': '식물 전문가나 가든센터에 상담을 받아보세요. 적절한 치료가 필요할 수 있습니다.'
    }
    return recommendations.get(health_status, '식물 상태를 주의 깊게 관찰하세요.')

# -------------------------- 병충해/질병 분류기 API (통합) - 건강 상태 우선 확인
@app.post("/disease")
async def classify_disease(
    image: UploadFile = File(...)
):
    """
    식물의 건강 상태를 먼저 확인하고, 문제가 있을 때만 병충해 진단 수행
    """
    try:
        # 업로드된 이미지 읽기
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        print(f"[DEBUG] 이미지 크기: {pil_image.size}")
        print(f"[DEBUG] 이미지 모드: {pil_image.mode}")
        
        # 1단계: 건강 상태 확인
        if health_model is None:
            raise HTTPException(status_code=500, detail="건강 상태 분류 모델이 로드되지 않았습니다.")
        
        print(f"[DEBUG] 건강 상태 확인 시작...")
        health_result = predict_health(pil_image, topk=1)
        health_status = health_result['class_name']
        health_confidence = health_result['score']
        
        print(f"[DEBUG] 건강 상태: {health_status}, 신뢰도: {health_confidence}")
        
        # 2단계: 건강한 경우
        if health_status == 'healthy':
            return JSONResponse(content={
                'success': True,
                'health_check': True,
                'health_status': health_status,
                'health_confidence': round(health_confidence, 4),
                'message': '건강한 식물입니다!',
                'recommendation': '현재 상태를 유지하세요. 정기적인 물주기와 햇빛을 제공하세요.',
                'disease_predictions': []
            })
        
        # 3단계: 건강하지 않은 경우 - 병충해 진단 수행
        print(f"[DEBUG] 건강하지 않음 - 병충해 진단 시작...")
        
        if pest_model is None:
            # 병충해 모델이 없는 경우 건강 상태만 반환
            return JSONResponse(content={
                'success': True,
                'health_check': True,
                'health_status': health_status,
                'health_confidence': round(health_confidence, 4),
                'message': f'식물에 문제가 있을 수 있습니다. (상태: {health_status})',
                'recommendation': '식물 전문가나 가든센터에 상담을 받아보세요.',
                'disease_predictions': []
            })
        
        # 병충해 분류 수행
        try:
            preds, msg = predict_pest(pil_image)
            print(f"[DEBUG] 병충해 예측 결과: {preds}")
            print(f"[DEBUG] 메시지: {msg}")
        except Exception as e:
            print(f"[DEBUG] predict_pest 오류: {e}")
            import traceback
            print(f"[DEBUG] 트레이스백: {traceback.format_exc()}")
            raise e
        
        # 예측 결과 처리
        disease_predictions = []
        if preds and len(preds) > 0:
            for i, pred in enumerate(preds[:3]):
                class_name = pred[0]
                confidence = pred[1]
                disease_predictions.append({
                    'class_name': class_name,
                    'confidence': round(confidence, 4),
                    'rank': i + 1
                })
        
        return JSONResponse(content={
            'success': True,
            'health_check': True,
            'health_status': health_status,
            'health_confidence': round(health_confidence, 4),
            'message': f'식물에 문제가 감지되었습니다. (상태: {health_status})',
            'recommendation': '아래 진단 결과를 참고하여 적절한 조치를 취하세요.',
            'disease_predictions': disease_predictions,
            'all_predictions': [{'class_name': pred[0], 'confidence': round(pred[1], 4)} for pred in preds[:3]]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"병충해/질병 분류 중 오류가 발생했습니다: {str(e)}")

# -------------------------- LLM 처리 API
from llm.src.orchestrator import plant_talk

from pydantic import BaseModel
from typing import Optional

class LLMRequest(BaseModel):
    species: str
    user_text: str
    moisture: Optional[float] = None

@app.post("/llm")
async def process_with_llm(request: LLMRequest):
    """
    LLM을 사용한 식물 대화 처리
    """
    try:
        result = plant_talk(request.species, request.user_text, request.moisture)
        
        return JSONResponse(content={
            'success': True,
            'message': 'LLM 처리 완료',
            'mode': result.mode,
            'species': result.species,
            'state': result.state,
            'reply': result.reply
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'message': f'LLM 처리 중 오류가 발생했습니다: {str(e)}',
            'error': 'llm_processing_error'
        })

# -------------------------- 헬스 체크 API
@app.get("/")
async def root():
    return {"message": "Plant AI API is running!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": {
            "segmentation": False,  # 호환성 문제로 비활성화됨
            "species": True,  # 새로운 모델 구조 사용
            "health": health_model is not None,
            "disease": pest_model is not None,  # 병충해/질병 통합 모델
            "llm": False  # 비활성화됨
        },
        "device": device,
        "available_classes": {
            "species": CLASSES,  # 새로운 모델 구조 사용
            "health": ["healthy", "unhealthy", "diseased"] if health_model is not None else []
        },
        "api_endpoints": [
            "POST /detector - 잎 탐지 및 세그멘테이션 (비활성화됨)",
            "POST /species - 품종 분류",
            "POST /health - 건강 상태 분류", 
            "POST /disease - 병충해/질병 분류 (통합)",
            "POST /llm - 식물 관련 질문 답변 (비활성화됨)",
            "GET /health - API 상태 확인"
        ]
    }
    

# -------------------------- 습도 코치 API

@app.get("/humidmeta")
def meta():
    m = {k: META[k] for k in ["version", "feat_cols", "S_DRY", "S_REF_DEFAULT"]}
    m["eta_calibration"] = META.get("eta_calibration")
    return m

@app.post("/predict", response_model=PredictResp)
def predict(req: PredictReq):
    S_ref = float(req.S_ref) if req.S_ref is not None else S_REF_DEFAULT
    if S_ref - S_DRY < 5:  # 너무 좁은 정규화 방지
        raise HTTPException(400, detail="S_ref와 S_dry 차이가 너무 작습니다. 앵커를 점검하세요.")
    eta, Rn, Rm, rhat = hours_until_threshold(req.S_now, req.S_min_user, req.temp_C, req.hour_of_day, S_ref)
    eta_cal, used_cal = apply_eta_calibration(eta)
    return PredictResp(
        eta_h=float(round(eta_cal, 2)),
        rstar_now=float(round(Rn, 4)),
        rstar_min=float(round(Rm, 4)),
        loss_rate_per_h=float(round(rhat, 6)),
        used_S_ref=float(round(S_ref, 2)),
        calibrated=bool(used_cal),
    )
