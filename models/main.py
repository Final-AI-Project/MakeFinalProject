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
from classifier.cascade.cascade import build_model
from classifier.pestcase.plant_classifier import predict_image as predict_pest

# 품종 분류 클래스 정의
CLASSES = [
    "monstera","stuckyi_sansevieria","zz_plant","cactus_succulent","phalaenopsis",
    "chamaedorea","schefflera","spathiphyllum","lady_palm","ficus_audrey",
    "olive_tree","dieffenbachia","boston_fern"
]
from healthy.healthy import predict_image as predict_health

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

# -------------------- 디바이스 결정 --------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Device: {device}")

# -------------------- 모델 로딩 --------------------
print("🔧 Loading Leaf Segmentation Model...")
print("⚠️ 세그멘테이션 모델 사용 중지됨 (호환성 문제)")
seg_model = None

# 품종 분류 모델 로드
print("🔧 Loading Species Classification Model...")
try:
    if os.path.exists(SPECIES_MODEL_PATH):
        species_model, _ = build_model("efficientnet_b0", len(CLASSES), 224)
        checkpoint = torch.load(SPECIES_MODEL_PATH, map_location=device)
        species_model.load_state_dict(checkpoint["model"])
        species_model.to(device)
        species_model.eval()
        print("✅ 품종 분류 모델 로드 완료")
    else:
        print("⚠️ 품종 분류 모델 파일이 없습니다. 더미 모델을 생성합니다.")
        species_model, _ = build_model("efficientnet_b0", len(CLASSES), 224)
        species_model.to(device)
        species_model.eval()
except Exception as e:
    print(f"❌ 품종 분류 모델 로드 실패: {e}")
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
    if species_model is None:
        raise HTTPException(status_code=500, detail="품종 분류 모델이 로드되지 않았습니다.")
    
    try:
        # 업로드된 이미지 읽기
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # 이미지 전처리 (EfficientNet B0용)
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        input_tensor = transform(pil_image).unsqueeze(0).to(device)
        
        # 예측 수행
        with torch.no_grad():
            outputs = species_model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            # 상위 3개 예측 결과
            top3_probs, top3_indices = torch.topk(probabilities, 3, dim=1)
            
            predictions = []
            for i in range(3):
                class_idx = top3_indices[0][i].item()
                class_name = CLASSES[class_idx]
                confidence_score = top3_probs[0][i].item()
                predictions.append({
                    'class_name': class_name,
                    'confidence': round(confidence_score, 4)
                })
        
        return JSONResponse(content={
            'success': True,
            'message': f"품종 분류 완료: {predictions[0]['class_name']}",
            'species': predictions[0]['class_name'],
            'confidence': predictions[0]['confidence'],
            'top_predictions': predictions
        })
        
    except Exception as e:
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

# -------------------------- 병충해/질병 분류기 API (통합)
@app.post("/disease")
async def classify_disease(
    image: UploadFile = File(...)
):
    """
    식물의 병충해/질병을 분류
    """
    if pest_model is None:
        # 병충해 모델이 없는 경우 건강 상태 모델을 활용
        if health_model is None:
            raise HTTPException(status_code=500, detail="병충해/질병 분류 모델이 로드되지 않았습니다.")
        
        try:
            # 건강 상태 모델을 사용하여 질병 여부 판단
            image_data = await image.read()
            pil_image = Image.open(io.BytesIO(image_data))
            
            result = predict_health(pil_image, topk=1)
            health_status = result['class_name']
            confidence = result['score']
            
            # 건강 상태를 기반으로 질병 여부 판단
            if health_status == 'diseased':
                disease_info = {
                    'disease': 'possible_disease',
                    'confidence': confidence,
                    'message': '식물에 질병이 있을 가능성이 있습니다.',
                    'recommendation': '식물 전문가나 가든센터에 상담을 받아보세요.'
                }
            else:
                disease_info = {
                    'disease': 'no_disease',
                    'confidence': confidence,
                    'message': '현재 질병의 징후가 보이지 않습니다.',
                    'recommendation': '정기적인 관찰을 계속하세요.'
                }
            
            return JSONResponse(content={
                'success': True,
                'message': disease_info['message'],
                'disease': disease_info['disease'],
                'confidence': round(disease_info['confidence'], 4),
                'recommendation': disease_info['recommendation'],
                'note': '건강 상태 모델을 사용한 예비 진단입니다.'
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"병충해/질병 분류 중 오류가 발생했습니다: {str(e)}")
    
    # 병충해 모델을 사용하여 병충해/질병 분류
    try:
        # 업로드된 이미지 읽기
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # 병충해 분류 수행 (질병 정보 포함)
        preds, msg = predict_pest(pil_image)
        
        # 예측 결과 처리
        if preds and len(preds) > 0:
            top_pred = preds[0]
            class_name = top_pred[0]
            confidence = top_pred[1]
        else:
            class_name = "unknown"
            confidence = 0.0
        
        return JSONResponse(content={
            'success': True,
            'message': f"병충해/질병 분류 완료: {class_name}",
            'disease': class_name,
            'confidence': round(confidence, 4),
            'disease_info': {
                'description': f"{class_name} 병충해가 감지되었습니다.",
                'treatment': '식물 전문가에게 상담하세요.',
                'prevention': '정기적인 관찰과 관리가 필요합니다.'
            },
            'recommendation': msg,
            'all_predictions': [{'class_name': pred[0], 'confidence': round(pred[1], 4)} for pred in preds[:3]]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"병충해/질병 분류 중 오류가 발생했습니다: {str(e)}")

# -------------------------- LLM 처리 API
from llm.src.orchestrator import plant_talk

@app.post("/llm")
async def process_with_llm(
    species: str,
    user_text: str,
    moisture: float = None
):
    """
    LLM을 사용한 식물 대화 처리
    """
    try:
        result = plant_talk(species, user_text, moisture)
        
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
            "species": species_model is not None,
            "health": health_model is not None,
            "disease": pest_model is not None,  # 병충해/질병 통합 모델
            "llm": False  # 비활성화됨
        },
        "device": device,
        "available_classes": {
            "species": CLASSES if species_model is not None else [],
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
    