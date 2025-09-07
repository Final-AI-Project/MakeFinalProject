"""
YOLOv8-Seg 모델 로딩 및 추론 유틸리티
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def load_yolo_seg_model(weights_path: str, device: str = "0") -> YOLO:
    """
    YOLOv8-Seg 모델을 로드합니다.
    
    Args:
        weights_path: 모델 가중치 파일 경로 (.pt)
        device: 사용할 디바이스 ("0", "1", "cpu")
    
    Returns:
        YOLO: 로드된 모델 객체
    
    Raises:
        FileNotFoundError: 모델 파일이 존재하지 않을 때
        Exception: 모델 로딩 실패 시
    """
    try:
        model = YOLO(weights_path)
        model.to(device)
        logger.info(f"모델 로드 완료: {weights_path}, 디바이스: {device}")
        return model
    except FileNotFoundError:
        logger.error(f"모델 파일을 찾을 수 없습니다: {weights_path}")
        raise
    except Exception as e:
        logger.error(f"모델 로딩 실패: {e}")
        raise


def infer_image(
    model: YOLO, 
    image: np.ndarray, 
    imgsz: int = 640, 
    conf: float = 0.25, 
    iou: float = 0.45, 
    max_det: int = 200
) -> List[Dict]:
    """
    이미지에서 YOLOv8-Seg 추론을 수행합니다.
    
    Args:
        model: YOLO 모델 객체
        image: 입력 이미지 (BGR 형식)
        imgsz: 입력 이미지 크기
        conf: 신뢰도 임계값
        iou: NMS IoU 임계값
        max_det: 최대 탐지 개수
    
    Returns:
        List[Dict]: 탐지 결과 리스트
        각 Dict는 다음 키를 포함:
        - "cls": 클래스 ID (int)
        - "conf": 신뢰도 (float)
        - "bbox_xyxy": 바운딩 박스 [x1, y1, x2, y2] (List[float])
        - "mask": 마스크 배열 (np.ndarray, bool)
        - "polygon": 폴리곤 좌표 리스트 (List[Tuple[int, int]])
    """
    try:
        # YOLO 추론 수행
        results = model(image, imgsz=imgsz, conf=conf, iou=iou, max_det=max_det)
        
        detections = []
        
        for result in results:
            if result.masks is not None:
                # 마스크가 있는 경우
                for i, (mask, box, conf_score, cls_id) in enumerate(
                    zip(result.masks.data, result.boxes.xyxy, result.boxes.conf, result.boxes.cls)
                ):
                    # 마스크를 원본 이미지 크기로 리사이즈
                    mask_resized = cv2.resize(
                        mask.cpu().numpy().astype(np.uint8), 
                        (image.shape[1], image.shape[0])
                    ).astype(bool)
                    
                    # 폴리곤 추출
                    polygon = _mask_to_polygon(mask_resized)
                    
                    detection = {
                        "cls": int(cls_id.cpu().numpy()),
                        "conf": float(conf_score.cpu().numpy()),
                        "bbox_xyxy": box.cpu().numpy().tolist(),
                        "mask": mask_resized,
                        "polygon": polygon
                    }
                    detections.append(detection)
            else:
                # 마스크가 없는 경우 (바운딩 박스만)
                for box, conf_score, cls_id in zip(
                    result.boxes.xyxy, result.boxes.conf, result.boxes.cls
                ):
                    detection = {
                        "cls": int(cls_id.cpu().numpy()),
                        "conf": float(conf_score.cpu().numpy()),
                        "bbox_xyxy": box.cpu().numpy().tolist(),
                        "mask": None,
                        "polygon": None
                    }
                    detections.append(detection)
        
        logger.info(f"탐지 완료: {len(detections)}개 객체")
        return detections
        
    except Exception as e:
        logger.error(f"추론 실패: {e}")
        return []


def _mask_to_polygon(mask: np.ndarray) -> List[Tuple[int, int]]:
    """
    마스크에서 폴리곤 좌표를 추출합니다.
    
    Args:
        mask: 이진 마스크 (bool 배열)
    
    Returns:
        List[Tuple[int, int]]: 폴리곤 좌표 리스트
    """
    try:
        # 마스크를 uint8로 변환
        mask_uint8 = (mask * 255).astype(np.uint8)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return []
        
        # 가장 큰 컨투어 선택
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 컨투어를 단순화
        epsilon = 0.002 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # 좌표를 튜플 리스트로 변환
        polygon = [(int(point[0][0]), int(point[0][1])) for point in approx]
        
        return polygon
        
    except Exception as e:
        logger.warning(f"폴리곤 추출 실패: {e}")
        return []


def preprocess_image(image_path: str) -> Optional[np.ndarray]:
    """
    이미지를 전처리합니다.
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        np.ndarray: 전처리된 이미지 (BGR 형식) 또는 None
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.warning(f"이미지 로드 실패: {image_path}")
            return None
        
        logger.debug(f"이미지 로드 성공: {image_path}, 크기: {image.shape}")
        return image
        
    except Exception as e:
        logger.error(f"이미지 전처리 실패: {e}")
        return None


def postprocess_detections(
    detections: List[Dict], 
    min_mask_area: int = 32
) -> List[Dict]:
    """
    탐지 결과를 후처리합니다.
    
    Args:
        detections: 탐지 결과 리스트
        min_mask_area: 최소 마스크 면적
    
    Returns:
        List[Dict]: 필터링된 탐지 결과
    """
    filtered_detections = []

    for detection in detections:
        # 마스크가 있는 경우 면적 체크
        if detection["mask"] is not None:
            mask_area = np.sum(detection["mask"])
            if mask_area < min_mask_area:
                logger.debug(f"작은 마스크 필터링: 면적 {mask_area}")
                continue
        
        filtered_detections.append(detection)
    
    logger.info(f"후처리 완료: {len(detections)} -> {len(filtered_detections)}")
    return filtered_detections
