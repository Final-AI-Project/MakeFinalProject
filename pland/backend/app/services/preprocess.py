"""
Image Preprocessing Service
이미지 전처리 및 리프 세그멘테이션
"""

import os
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """이미지 전처리 클래스"""
    
    def __init__(self, target_size: int = 512):
        """
        초기화
        
        Args:
            target_size: 목표 이미지 크기
        """
        self.target_size = target_size
        self.rembg_model = None
        
    async def _load_rembg_model(self):
        """U²-Net 기반 배경 제거 모델 로드"""
        if self.rembg_model is None:
            try:
                from rembg import remove
                self.rembg_model = remove
                logger.info("U²-Net 배경 제거 모델 로드 완료")
            except ImportError:
                logger.warning("rembg가 설치되지 않았습니다. 배경 제거를 건너뜁니다.")
                self.rembg_model = None
    
    async def preprocess_image(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[str], Dict[str, Any]]:
        """
        이미지 전처리 메인 함수
        
        Args:
            image_path: 입력 이미지 경로
            
        Returns:
            processed_image: 전처리된 이미지
            mask_path: 마스크 파일 경로 (저장된 경우)
            crop_info: 크롭 정보
        """
        try:
            # 이미지 로드
            original_image = await self._load_image(image_path)
            if original_image is None:
                return None, None, {}
            
            # 배경 제거
            processed_image, mask = await self._remove_background(original_image)
            
            # 리프 영역 크롭
            cropped_image, crop_info = await self._crop_leaf_region(processed_image, mask)
            
            # 리사이즈
            resized_image = await self._resize_image(cropped_image)
            
            # 마스크 저장 (디버깅용)
            mask_path = None
            if mask is not None:
                mask_path = await self._save_mask(mask, image_path)
            
            return resized_image, mask_path, crop_info
            
        except Exception as e:
            logger.error(f"이미지 전처리 중 오류: {str(e)}")
            # 오류 발생 시 원본 이미지 리사이즈만 수행
            try:
                original_image = await self._load_image(image_path)
                if original_image is not None:
                    resized_image = await self._resize_image(original_image)
                    return resized_image, None, {"error": str(e)}
            except:
                pass
            return None, None, {"error": str(e)}
    
    async def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """이미지 로드"""
        try:
            # PIL로 로드 후 numpy로 변환
            pil_image = Image.open(image_path)
            # RGBA를 RGB로 변환
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            image = np.array(pil_image)
            return image
        except Exception as e:
            logger.error(f"이미지 로드 실패: {str(e)}")
            return None
    
    async def _remove_background(self, image: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """배경 제거"""
        try:
            await self._load_rembg_model()
            
            if self.rembg_model is not None:
                # rembg를 사용한 배경 제거
                pil_image = Image.fromarray(image)
                result = self.rembg_model(pil_image)
                
                # 결과를 numpy 배열로 변환
                result_array = np.array(result)
                
                # 알파 채널이 있으면 마스크 추출
                mask = None
                if result_array.shape[-1] == 4:
                    mask = result_array[:, :, 3] > 0
                    # RGB만 사용
                    result_array = result_array[:, :, :3]
                
                return result_array, mask
            else:
                # rembg가 없으면 원본 반환
                return image, None
                
        except Exception as e:
            logger.warning(f"배경 제거 실패, 원본 사용: {str(e)}")
            return image, None
    
    async def _crop_leaf_region(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """리프 영역 크롭"""
        try:
            if mask is not None:
                # 마스크를 사용한 크롭
                coords = cv2.findNonZero(mask.astype(np.uint8))
                if coords is not None:
                    x, y, w, h = cv2.boundingRect(coords)
                    cropped = image[y:y+h, x:x+w]
                    crop_info = {
                        "method": "mask_based",
                        "bbox": [x, y, w, h],
                        "original_size": image.shape[:2],
                        "cropped_size": cropped.shape[:2]
                    }
                    return cropped, crop_info
            
            # 마스크가 없으면 전체 이미지 사용
            crop_info = {
                "method": "full_image",
                "bbox": [0, 0, image.shape[1], image.shape[0]],
                "original_size": image.shape[:2],
                "cropped_size": image.shape[:2]
            }
            return image, crop_info
            
        except Exception as e:
            logger.warning(f"리프 크롭 실패, 원본 사용: {str(e)}")
            crop_info = {
                "method": "error_fallback",
                "bbox": [0, 0, image.shape[1], image.shape[0]],
                "original_size": image.shape[:2],
                "cropped_size": image.shape[:2],
                "error": str(e)
            }
            return image, crop_info
    
    async def _resize_image(self, image: np.ndarray) -> np.ndarray:
        """이미지 리사이즈"""
        try:
            # PIL을 사용한 리사이즈 (더 나은 품질)
            pil_image = Image.fromarray(image)
            pil_image = pil_image.resize((self.target_size, self.target_size), Image.Resampling.LANCZOS)
            resized_image = np.array(pil_image)
            return resized_image
        except Exception as e:
            logger.error(f"이미지 리사이즈 실패: {str(e)}")
            return image
    
    async def _save_mask(self, mask: np.ndarray, original_path: str) -> Optional[str]:
        """마스크 저장 (디버깅용)"""
        try:
            # 마스크 저장 경로 생성
            base_name = os.path.splitext(os.path.basename(original_path))[0]
            mask_dir = os.path.join("storage", "uploads", "masks")
            os.makedirs(mask_dir, exist_ok=True)
            mask_path = os.path.join(mask_dir, f"{base_name}_mask.png")
            
            # 마스크를 이미지로 저장
            mask_image = (mask * 255).astype(np.uint8)
            cv2.imwrite(mask_path, mask_image)
            
            return mask_path
        except Exception as e:
            logger.warning(f"마스크 저장 실패: {str(e)}")
            return None
    
    def get_preprocessing_pipeline(self) -> Dict[str, Any]:
        """전처리 파이프라인 정보 반환"""
        return {
            "target_size": self.target_size,
            "background_removal": "U²-Net (rembg)",
            "leaf_cropping": "Mask-based bounding box",
            "resizing": "Lanczos interpolation",
            "supported_formats": ["jpg", "jpeg", "png", "webp"]
        }
