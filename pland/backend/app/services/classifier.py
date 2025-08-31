"""
Plant Classifier Service
식물 품종 및 질병 분류
"""

import os
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional
import logging
import timm
from torchvision import transforms

logger = logging.getLogger(__name__)


class PlantClassifier:
    """식물 분류기 클래스"""
    
    def __init__(
        self,
        model_name: str = "efficientnet_b0",
        device: str = "cpu",
        use_onnx: bool = False,
        model_path: Optional[str] = None
    ):
        """
        초기화
        
        Args:
            model_name: 모델 이름
            device: 추론 디바이스
            use_onnx: ONNX 런타임 사용 여부
            model_path: 모델 파일 경로
        """
        self.model_name = model_name
        self.device = device
        self.use_onnx = use_onnx
        self.model_path = model_path
        self.model = None
        self.onnx_session = None
        self.class_names = self._get_default_class_names()
        
        # 전처리 파이프라인
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 모델 로드
        self._load_model()
    
    def _get_default_class_names(self) -> Dict[str, List[str]]:
        """기본 클래스명 반환"""
        return {
            "species": [
                "토마토", "고추", "상추", "양파", "마늘", "당근", "감자", "고구마",
                "배추", "무", "오이", "호박", "가지", "피망", "브로콜리", "양배추",
                "시금치", "부추", "파", "생강", "우엉", "연근", "미나리", "깻잎",
                "바질", "로즈마리", "라벤더", "민트", "레몬그라스", "타임"
            ],
            "disease": [
                "건강", "세균성점무늬병", "세균성시들음병", "세균성썩음병",
                "검은점무늬병", "노균병", "흰가루병", "잎마름병", "바이러스병",
                "선충병", "곰팡이병", "탄저병", "역병", "겹무늬병", "점무늬병"
            ]
        }
    
    def _load_model(self):
        """모델 로드"""
        try:
            if self.use_onnx and self.model_path and self.model_path.endswith('.onnx'):
                self._load_onnx_model()
            else:
                self._load_pytorch_model()
        except Exception as e:
            logger.error(f"모델 로드 실패: {str(e)}")
            # 기본 모델로 폴백
            self._load_default_model()
    
    def _load_onnx_model(self):
        """ONNX 모델 로드"""
        try:
            import onnxruntime as ort
            self.onnx_session = ort.InferenceSession(self.model_path)
            logger.info(f"ONNX 모델 로드 완료: {self.model_path}")
        except Exception as e:
            logger.error(f"ONNX 모델 로드 실패: {str(e)}")
            raise
    
    def _load_pytorch_model(self):
        """PyTorch 모델 로드"""
        try:
            if self.model_path and os.path.exists(self.model_path):
                # 저장된 모델 로드
                checkpoint = torch.load(self.model_path, map_location=self.device)
                if 'model_state_dict' in checkpoint:
                    self.model = self._create_model_architecture()
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.model = checkpoint
                logger.info(f"PyTorch 모델 로드 완료: {self.model_path}")
            else:
                # 기본 모델 로드
                self._load_default_model()
        except Exception as e:
            logger.error(f"PyTorch 모델 로드 실패: {str(e)}")
            self._load_default_model()
    
    def _load_default_model(self):
        """기본 모델 로드 (사전학습된 모델)"""
        try:
            self.model = timm.create_model(
                self.model_name,
                pretrained=True,
                num_classes=len(self.class_names["species"]) + len(self.class_names["disease"])
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"기본 모델 로드 완료: {self.model_name}")
        except Exception as e:
            logger.error(f"기본 모델 로드 실패: {str(e)}")
            raise
    
    def _create_model_architecture(self):
        """모델 아키텍처 생성"""
        # 멀티헤드 분류기 (품종 + 질병)
        num_species = len(self.class_names["species"])
        num_diseases = len(self.class_names["disease"])
        
        model = timm.create_model(
            self.model_name,
            pretrained=False,
            num_classes=num_species + num_diseases
        )
        model.to(self.device)
        model.eval()
        return model
    
    async def classify_species(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        품종 분류
        
        Args:
            image: 입력 이미지
            
        Returns:
            품종 분류 결과 (Top-K)
        """
        try:
            if self.use_onnx and self.onnx_session:
                predictions = await self._inference_onnx(image)
            else:
                predictions = await self._inference_pytorch(image)
            
            # 품종 예측 추출 (첫 번째 헤드)
            num_species = len(self.class_names["species"])
            species_logits = predictions[:num_species]
            
            # 확률 계산
            species_probs = F.softmax(torch.tensor(species_logits), dim=0).numpy()
            
            # Top-K 결과 생성
            top_indices = np.argsort(species_probs)[::-1]
            results = []
            
            for idx in top_indices:
                results.append({
                    "class": self.class_names["species"][idx],
                    "confidence": float(species_probs[idx]),
                    "rank": len(results) + 1
                })
            
            return results
            
        except Exception as e:
            logger.error(f"품종 분류 실패: {str(e)}")
            return []
    
    async def classify_disease(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        질병 분류
        
        Args:
            image: 입력 이미지
            
        Returns:
            질병 분류 결과 (Top-K)
        """
        try:
            if self.use_onnx and self.onnx_session:
                predictions = await self._inference_onnx(image)
            else:
                predictions = await self._inference_pytorch(image)
            
            # 질병 예측 추출 (두 번째 헤드)
            num_species = len(self.class_names["species"])
            num_diseases = len(self.class_names["disease"])
            disease_logits = predictions[num_species:num_species + num_diseases]
            
            # 확률 계산
            disease_probs = F.softmax(torch.tensor(disease_logits), dim=0).numpy()
            
            # Top-K 결과 생성
            top_indices = np.argsort(disease_probs)[::-1]
            results = []
            
            for idx in top_indices:
                results.append({
                    "class": self.class_names["disease"][idx],
                    "confidence": float(disease_probs[idx]),
                    "rank": len(results) + 1
                })
            
            return results
            
        except Exception as e:
            logger.error(f"질병 분류 실패: {str(e)}")
            return []
    
    async def _inference_onnx(self, image: np.ndarray) -> np.ndarray:
        """ONNX 추론"""
        try:
            # 이미지 전처리
            pil_image = Image.fromarray(image)
            input_tensor = self.transform(pil_image).unsqueeze(0).numpy()
            
            # ONNX 추론
            input_name = self.onnx_session.get_inputs()[0].name
            output_name = self.onnx_session.get_outputs()[0].name
            predictions = self.onnx_session.run([output_name], {input_name: input_tensor})[0]
            
            return predictions[0]  # 배치 차원 제거
            
        except Exception as e:
            logger.error(f"ONNX 추론 실패: {str(e)}")
            raise
    
    async def _inference_pytorch(self, image: np.ndarray) -> np.ndarray:
        """PyTorch 추론"""
        try:
            # 이미지 전처리
            pil_image = Image.fromarray(image)
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            # 추론
            with torch.no_grad():
                predictions = self.model(input_tensor)
                predictions = predictions.cpu().numpy()[0]  # 배치 차원 제거
            
            return predictions
            
        except Exception as e:
            logger.error(f"PyTorch 추론 실패: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "use_onnx": self.use_onnx,
            "model_path": self.model_path,
            "num_species_classes": len(self.class_names["species"]),
            "num_disease_classes": len(self.class_names["disease"]),
            "total_classes": len(self.class_names["species"]) + len(self.class_names["disease"])
        }
