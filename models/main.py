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
from detector.leaf_segmentation import LeafSegmentationModel
from classifier.plant_classifier import build_model, CLASSES
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
SPECIES_MODEL_PATH = "weight/efficientnet_b0_dummy_best.pth"  # 품종 분류 모델
HEALTH_MODEL_PATH = "healthy/healthy.pt"    # 건강 상태 모델
DISEASE_MODEL_PATH = "weight/disease_model.pt"  # 질병 분류 모델 (미구현)

# -------------------- 디바이스 결정 --------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Device: {device}")

# -------------------- 모델 로딩 --------------------
print("🔧 Loading Leaf Segmentation Model...")
try:
    seg_model = LeafSegmentationModel(SEG_MODEL_PATH)
    print("✅ 세그멘테이션 모델 로드 완료")
except Exception as e:
    print(f"❌ 세그멘테이션 모델 로드 실패: {e}")
    seg_model = None

# 품종 분류 모델 로드
print("🔧 Loading Species Classification Model...")
try:
    if os.path.exists(SPECIES_MODEL_PATH):
        species_model, _ = build_model("efficientnet_b0", len(CLASSES))
        checkpoint = torch.load(SPECIES_MODEL_PATH, map_location=device)
        species_model.load_state_dict(checkpoint["model"])
        species_model.to(device)
        species_model.eval()
        print("✅ 품종 분류 모델 로드 완료")
    else:
        print("⚠️ 품종 분류 모델 파일이 없습니다. 더미 모델을 생성합니다.")
        species_model, _ = build_model("efficientnet_b0", len(CLASSES))
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

# 질병 분류 모델 (미구현)
disease_model = None

# -------------------------- 잎 탐지 및 세그멘테이션 API
@app.post("/detector")
async def detect_and_segment_leaves(
    image: UploadFile = File(...)
):
    """
    이미지에서 식물의 잎을 탐지하고 세그멘테이션하여 크롭된 잎 이미지들을 반환
    """
    if seg_model is None:
        raise HTTPException(status_code=500, detail="세그멘테이션 모델이 로드되지 않았습니다.")
    
    try:
        # 업로드된 이미지 읽기
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # 세그멘테이션 수행
        results = seg_model.predict(pil_image)
        
        # 크롭된 잎 이미지들을 base64로 인코딩
        cropped_images_base64 = []
        for i, cropped_leaf in enumerate(results['cropped_leaves']):
            # PIL Image를 base64로 변환
            buffer = io.BytesIO()
            cropped_leaf.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            import base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            cropped_images_base64.append({
                'index': i,
                'image': img_base64,
                'format': 'jpeg'
            })
        
        # 세그멘테이션된 이미지도 base64로 인코딩
        buffer = io.BytesIO()
        results['segmented_image'].save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        segmented_img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return JSONResponse(content={
            'success': True,
            'message': f"{len(results['cropped_leaves'])}개의 잎이 탐지되었습니다.",
            'detected_leaves_count': len(results['cropped_leaves']),
            'cropped_leaves': cropped_images_base64,
            'segmented_image': {
                'image': segmented_img_base64,
                'format': 'jpeg'
            },
            'bounding_boxes': results['boxes']
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")

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
        pil_image = Image.open(io.BytesIO(image_data))
        
        # 이미지 전처리 (EfficientNet B0용)
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.Resize(256),
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

# -------------------------- 질병 분류기 API
@app.post("/disease")
async def classify_disease(
    image: UploadFile = File(...)
):
    """
    식물의 질병을 분류
    """
    if disease_model is None:
        # 질병 분류 모델이 없는 경우 건강 상태 모델을 활용
        if health_model is None:
            raise HTTPException(status_code=500, detail="질병 분류 모델이 로드되지 않았습니다.")
        
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
            raise HTTPException(status_code=500, detail=f"질병 분류 중 오류가 발생했습니다: {str(e)}")
    
    # TODO: 전용 질병 분류 모델이 있을 때의 구현
    return JSONResponse(content={
        'success': True,
        'message': '전용 질병 분류 모델 구현 예정입니다.',
        'disease': 'unknown'
    })

# -------------------------- LLM 처리 API
@app.post("/llm")
async def process_with_llm(
    text: str
):
    """
    LLM을 사용한 텍스트 처리 (식물 관련 질문 답변)
    """
    try:
        # 간단한 규칙 기반 응답 시스템 (실제 LLM 모델 대신)
        response = generate_plant_response(text)
        
        return JSONResponse(content={
            'success': True,
            'message': '식물 관련 질문에 대한 답변을 제공합니다.',
            'response': response,
            'note': '현재는 규칙 기반 응답 시스템을 사용합니다. 실제 LLM 모델 구현 예정입니다.'
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 처리 중 오류가 발생했습니다: {str(e)}")

def generate_plant_response(text: str) -> str:
    """식물 관련 질문에 대한 규칙 기반 응답 생성"""
    text_lower = text.lower()
    
    # 물주기 관련
    if any(keyword in text_lower for keyword in ['물', 'water', '물주기', 'watering']):
        return "식물의 물주기는 종류에 따라 다릅니다. 일반적으로 토양이 마르면 충분히 물을 주되, 과습을 피하세요. 겨울에는 물주기 빈도를 줄이는 것이 좋습니다."
    
    # 햇빛 관련
    elif any(keyword in text_lower for keyword in ['햇빛', 'sunlight', '빛', 'light', '그늘']):
        return "대부분의 실내 식물은 밝은 간접광을 선호합니다. 직사광선은 잎을 태울 수 있으니 주의하세요. 식물 종류에 따라 햇빛 요구량이 다르니 확인해보세요."
    
    # 잎이 노랗게 변하는 경우
    elif any(keyword in text_lower for keyword in ['노란', 'yellow', '잎', 'leaf']):
        return "잎이 노랗게 변하는 것은 과습, 영양 부족, 또는 자연적인 노화 현상일 수 있습니다. 물주기 빈도와 토양 상태를 확인해보세요."
    
    # 식물 추천
    elif any(keyword in text_lower for keyword in ['추천', 'recommend', '어떤', 'what']):
        return "초보자에게는 몬스테라, 고무나무, 스투키 등이 좋습니다. 이들은 관리가 쉽고 실내 환경에 잘 적응합니다."
    
    # 일반적인 식물 관리
    else:
        return "식물 관리에 대한 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다. 물주기, 햇빛, 토양, 온도 등에 대해 궁금한 점이 있으시면 언제든 물어보세요."

# -------------------------- 헬스 체크 API
@app.get("/")
async def root():
    return {"message": "Plant AI API is running!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": {
            "segmentation": seg_model is not None,
            "species": species_model is not None,
            "health": health_model is not None,
            "disease": disease_model is not None
        },
        "device": device,
        "available_classes": {
            "species": CLASSES if species_model is not None else [],
            "health": ["healthy", "unhealthy", "diseased"] if health_model is not None else []
        },
        "api_endpoints": [
            "POST /detector - 잎 탐지 및 세그멘테이션",
            "POST /species - 품종 분류",
            "POST /health - 건강 상태 분류", 
            "POST /disease - 질병 분류",
            "POST /llm - 식물 관련 질문 답변",
            "GET /health - API 상태 확인"
        ]
    }
    