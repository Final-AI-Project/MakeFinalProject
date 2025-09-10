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
from detector.leaf_segmentation import LeafSegmentationModel

# ------ FastAPI 앱
app = FastAPI()

# ------ CORS
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- 모델 경로 설정
SEG_MODEL_PATH = "weight/seg_best.pt"
SPECIES_MODEL_PATH = "weight/species_model.pt"  # 필요시 경로 수정
HEALTH_MODEL_PATH = "weight/health_model.pt"    # 필요시 경로 수정
DISEASE_MODEL_PATH = "weight/disease_model.pt"  # 필요시 경로 수정

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

# 다른 모델들도 필요시 로드
# species_model = YOLO(SPECIES_MODEL_PATH) if os.path.exists(SPECIES_MODEL_PATH) else None
# health_model = YOLO(HEALTH_MODEL_PATH) if os.path.exists(HEALTH_MODEL_PATH) else None
# disease_model = YOLO(DISEASE_MODEL_PATH) if os.path.exists(DISEASE_MODEL_PATH) else None

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
    # TODO: 품종 분류 모델 구현
    return JSONResponse(content={
        'success': True,
        'message': '품종 분류 기능은 구현 예정입니다.',
        'species': 'unknown'
    })

# -------------------------- 잎 상태 분류기 API
@app.post("/health")
async def classify_health(
    image: UploadFile = File(...)
):
    """
    잎의 건강 상태를 분류
    """
    # TODO: 건강 상태 분류 모델 구현
    return JSONResponse(content={
        'success': True,
        'message': '건강 상태 분류 기능은 구현 예정입니다.',
        'health_status': 'unknown'
    })

# -------------------------- 질병 분류기 API
@app.post("/disease")
async def classify_disease(
    image: UploadFile = File(...)
):
    """
    식물의 질병을 분류
    """
    # TODO: 질병 분류 모델 구현
    return JSONResponse(content={
        'success': True,
        'message': '질병 분류 기능은 구현 예정입니다.',
        'disease': 'unknown'
    })

# -------------------------- LLM 처리 API
@app.post("/llm")
async def process_with_llm(
    text: str
):
    """
    LLM을 사용한 텍스트 처리
    """
    # TODO: LLM 모델 구현
    return JSONResponse(content={
        'success': True,
        'message': 'LLM 기능은 구현 예정입니다.',
        'response': 'LLM 응답 예정'
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
            "segmentation": seg_model is not None,
            "species": False,  # TODO: 모델 로드 상태 확인
            "health": False,   # TODO: 모델 로드 상태 확인
            "disease": False   # TODO: 모델 로드 상태 확인
        }
    }
    