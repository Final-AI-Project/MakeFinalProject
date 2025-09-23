"""
식물 분류 모델 클라이언트
"""
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import io
from typing import List, Dict, Any
import os
from pathlib import Path

# 모델 클래스 정의
class PlantClassifier(nn.Module):
    def __init__(self, num_classes: int = 13):
        super().__init__()
        # MobileNetV3-Large 백본 사용
        from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
        
        self.backbone = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        self.backbone.classifier = nn.Sequential(
            nn.Linear(self.backbone.classifier[0].in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)

# 식물 클래스 정의
PLANT_CLASSES = [
    "보스턴고사리",      # boston_fern
    "선인장",           # cactus_succulent  
    "관음죽",           # chamaedorea
    "디펜바키아",        # dieffenbachia
    "벵갈고무나무",      # ficus_audrey
    "테이블야자",        # lady_palm
    "몬스테라",          # monstera
    "올리브나무",        # olive_tree
    "호접란",           # phalaenopsis
    "홍콩야자",         # schefflera
    "스파티필럼",        # spathiphyllum
    "스투키",           # stuckyi_sansevieria
    "금전수"            # zz_plant
]

# 전역 모델 변수
_model = None
_device = None

def load_model():
    """모델 로드"""
    global _model, _device
    
    if _model is not None:
        return _model, _device
    
    try:
        # 모델 파일 경로
        model_path = Path(__file__).parent.parent.parent.parent / "models" / "classifier" / "plant_classifier" / "mobilenet_v3_large_best.pth"
        
        if not model_path.exists():
            print(f"[WARNING] 모델 파일을 찾을 수 없습니다: {model_path}")
            return None, None
        
        # 디바이스 설정
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[INFO] 식물 분류 모델 디바이스: {_device}")
        
        # 모델 로드
        _model = PlantClassifier(num_classes=len(PLANT_CLASSES))
        _model.load_state_dict(torch.load(model_path, map_location=_device, weights_only=False))
        _model.to(_device)
        _model.eval()
        
        print(f"[INFO] 식물 분류 모델 로드 완료: {model_path}")
        return _model, _device
        
    except Exception as e:
        print(f"[ERROR] 식물 분류 모델 로드 실패: {e}")
        return None, None

def get_transform():
    """이미지 전처리 변환"""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

async def classify_plant(image_data: bytes) -> Dict[str, Any]:
    """
    식물 이미지를 분류합니다.
    
    Args:
        image_data: 이미지 바이트 데이터
        
    Returns:
        분류 결과 딕셔너리
    """
    try:
        # 모델 로드
        model, device = load_model()
        if model is None:
            return {
                "success": False,
                "error": "모델을 로드할 수 없습니다.",
                "predictions": []
            }
        
        # 이미지 전처리
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        transform = get_transform()
        input_tensor = transform(image).unsqueeze(0).to(device)
        
        # 추론
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            top_probs, top_indices = torch.topk(probabilities, k=3, dim=1)
        
        # 결과 구성
        predictions = []
        for i in range(3):
            class_idx = top_indices[0][i].item()
            confidence = top_probs[0][i].item()
            
            predictions.append({
                "class_name": PLANT_CLASSES[class_idx],
                "confidence": confidence,
                "rank": i + 1
            })
        
        return {
            "success": True,
            "predictions": predictions,
            "top_prediction": predictions[0] if predictions else None
        }
        
    except Exception as e:
        print(f"[ERROR] 식물 분류 중 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "predictions": []
        }

def get_plant_classes() -> List[str]:
    """지원하는 식물 클래스 목록 반환"""
    return PLANT_CLASSES.copy()
