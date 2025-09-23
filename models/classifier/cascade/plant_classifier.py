"""
식물 분류 모델 - cascade 폴더 기반
가중치 경로: D:\Pland_predev2\models\classifier\cascade\weight\mobilenet_v3_large_best.pth
"""
import torch
import torch.nn as nn
from torchvision import transforms, models
from torchvision.models import MobileNet_V3_Large_Weights
from PIL import Image
import io
from typing import List, Dict, Any
import os
from pathlib import Path

def load_plant_classes() -> List[str]:
    """labels.txt 파일에서 식물 클래스 목록을 로드"""
    labels_path = Path(__file__).parent / "labels.txt"
    try:
        with open(labels_path, 'r', encoding='utf-8') as f:
            classes = [line.strip() for line in f.readlines() if line.strip()]
        print(f"[DEBUG] 로드된 클래스 수: {len(classes)}")
        print(f"[DEBUG] 클래스 목록: {classes}")
        return classes
    except Exception as e:
        print(f"[ERROR] 라벨 파일 로드 실패: {e}")
        # 기본값 반환 (labels.txt와 동일한 순서)
        return [
            "보스턴고사리", "선인장", "관음죽", "디펜바키아", "벵갈고무나무",
            "테이블야자", "몬스테라", "올리브나무", "호접란", "홍콩야자",
            "스파티필럼", "스투키", "금전수"
        ]

# 식물 클래스 정의 (labels.txt 기반)
PLANT_CLASSES = load_plant_classes()

def build_plant_model(model_name: str, num_classes: int):
    """원본 infer_classifier.py와 동일한 모델 빌드 함수"""
    name = model_name.lower()
    if name in ["mobilenet", "mobilenet_v3_large"]:
        m = models.mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    else:
        raise ValueError("지원하지 않는 모델명")
    return m, rec

def load_weights(model: nn.Module, weights_path: Path):
    """가중치 로드 함수"""
    print(f"[DEBUG] 가중치 파일 로드 시작: {weights_path}")
    ckpt = torch.load(str(weights_path), map_location="cpu")
    print(f"[DEBUG] 체크포인트 타입: {type(ckpt)}")
    
    if isinstance(ckpt, dict):
        print(f"[DEBUG] 체크포인트 키들: {list(ckpt.keys())}")
        if "state_dict" in ckpt:
            sd = ckpt["state_dict"]
            print("[DEBUG] state_dict 키에서 로드")
        elif "model" in ckpt:
            sd = ckpt["model"]
            print("[DEBUG] model 키에서 로드")
        else:
            sd = ckpt
            print("[DEBUG] 직접 딕셔너리에서 로드")
    else:
        try:
            model.load_state_dict(ckpt.state_dict())
            print("[INFO] loaded from full model object")
            return
        except Exception as e:
            raise RuntimeError(f"unknown checkpoint format: {type(ckpt)} {e}")

    print(f"[DEBUG] state_dict 키 개수: {len(sd)}")
    print(f"[DEBUG] state_dict 첫 5개 키: {list(sd.keys())[:5]}")
    
    # module. prefix 제거
    sd = { (k[7:] if k.startswith("module.") else k): v for k, v in sd.items() }
    print(f"[DEBUG] prefix 제거 후 첫 5개 키: {list(sd.keys())[:5]}")
    
    try:
        model.load_state_dict(sd, strict=True)
        print("[INFO] state_dict strict=True loaded")
    except Exception as e:
        print(f"[WARN] strict=True failed: {e}")
        model.load_state_dict(sd, strict=False)
        print("[INFO] state_dict strict=False loaded")

class PlantClassificationService:
    """식물 분류 서비스"""
    
    def __init__(self):
        self.model = None
        self.device = None
        self.transform = None
        self.classes = PLANT_CLASSES
        
    def load_model(self, model_path: str = None):
        """모델 로드"""
        try:
            if model_path is None:
                # 상대 경로로 가중치 파일 찾기
                current_dir = Path(__file__).parent
                model_path = current_dir / "weight" / "mobilenet_v3_large_best.pth"
                print(f"[DEBUG] 모델 경로: {model_path}")
                print(f"[DEBUG] 모델 경로 존재 여부: {os.path.exists(model_path)}")
            
            if not os.path.exists(model_path):
                print(f"[ERROR] 모델 파일을 찾을 수 없습니다: {model_path}")
                return False
            
            # 디바이스 설정
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"[INFO] 식물 분류 모델 디바이스: {self.device}")
            
            # 모델 빌드
            print(f"[DEBUG] 모델 빌드 시작...")
            self.model, rec = build_plant_model("mobilenet_v3_large", len(self.classes))
            print(f"[DEBUG] 모델 빌드 완료")
            
            # 가중치 로드
            print(f"[DEBUG] 가중치 로드 시작...")
            load_weights(self.model, Path(model_path))
            print(f"[DEBUG] 가중치 로드 완료")
            
            self.model.to(self.device)
            self.model.eval()
            print(f"[DEBUG] 모델 eval 모드 설정 완료")
            
            # 이미지 전처리 설정 (원본 infer_classifier.py와 동일)
            self.transform = transforms.Compose([
                transforms.Resize(int(224*1.14)),  # 256
                transforms.CenterCrop(224),        # 224
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            print(f"[INFO] 식물 분류 모델 로드 완료: {model_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 식물 분류 모델 로드 실패: {e}")
            import traceback
            print(f"[ERROR] 트레이스백: {traceback.format_exc()}")
            return False
    
    def predict(self, image_data: bytes) -> Dict[str, Any]:
        """
        식물 이미지 분류
        
        Args:
            image_data: 이미지 바이트 데이터
            
        Returns:
            분류 결과
        """
        print(f"[DEBUG] predict 메서드 호출됨")
        
        if self.model is None:
            print(f"[ERROR] 모델이 None입니다!")
            return {
                "success": False,
                "error": "모델이 로드되지 않았습니다.",
                "predictions": []
            }
        
        if self.transform is None:
            print(f"[ERROR] transform이 None입니다!")
            return {
                "success": False,
                "error": "이미지 전처리 변환이 설정되지 않았습니다.",
                "predictions": []
            }
        
        try:
            # 이미지 전처리
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            print(f"[DEBUG] 이미지 로드 완료: {img.size}")
            
            x = self.transform(img).unsqueeze(0).to(self.device)  # [1,3,224,224]
            print(f"[DEBUG] 텐서 변환 완료: {x.shape}")
            
            # 추론
            with torch.no_grad():
                logits = self.model(x)
                probs = torch.softmax(logits, dim=1)[0]
            
            # 결과 구성
            conf, idx = torch.max(probs, dim=0)
            species = self.classes[idx.item()]
            confidence = round(conf.item(), 4)
            
            # Top 3 예측 결과
            top_probs, top_indices = torch.topk(probs, k=3, dim=0)
            predictions = []
            for i in range(3):
                class_idx = top_indices[i].item()
                pred_confidence = top_probs[i].item()
                
                predictions.append({
                    "class_name": self.classes[class_idx],
                    "confidence": pred_confidence,
                    "rank": i + 1
                })
            
            return {
                "success": True,
                "predictions": predictions,
                "top_prediction": predictions[0] if predictions else None
            }
            
        except Exception as e:
            print(f"[ERROR] 식물 분류 중 오류: {e}")
            import traceback
            print(f"[ERROR] 트레이스백: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }
    
    def get_classes(self) -> List[str]:
        """지원하는 식물 클래스 목록 반환"""
        return self.classes.copy()

# 전역 서비스 인스턴스
_plant_service = None

def get_plant_service() -> PlantClassificationService:
    """식물 분류 서비스 인스턴스 반환"""
    global _plant_service
    if _plant_service is None:
        _plant_service = PlantClassificationService()
        success = _plant_service.load_model()
        if not success:
            print(f"[ERROR] 모델 로드 실패, 서비스 객체는 생성되었지만 모델이 None입니다.")
    return _plant_service

def build_plant_model_service():
    """기존 호환성을 위한 함수"""
    return get_plant_service()

def predict_plant_species(image_data: bytes) -> Dict[str, Any]:
    """식물 종 분류 (기존 API 호환)"""
    service = get_plant_service()
    return service.predict(image_data)
