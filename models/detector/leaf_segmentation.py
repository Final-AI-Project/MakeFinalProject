import torch
import cv2
import numpy as np
from PIL import Image
import io
from ultralytics import YOLO
import os

# === PyTorch 2.6 호환성을 위한 설정 ===
# torch.load의 weights_only를 False로 설정
torch.serialization.DEFAULT_PROTOCOL = 2

class LeafSegmentationModel:
    
    def __init__(self, model_path: str):
        """
        잎 세그멘테이션 모델 초기화
        
        Args:
            model_path (str): seg_best.pt 모델 파일 경로
        """
        self.model_path = model_path
        self.model = None
        self.device = self._get_device()
        self._load_model()
    
    def _get_device(self):
        """사용 가능한 디바이스 결정"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _load_model(self):
        """YOLO 세그멘테이션 모델 로드"""
        try:
            # PyTorch 2.6 호환성을 위한 설정
            import torch
            import pickle
            
            # torch.load를 임시로 수정
            original_load = torch.load
            original_pickle_load = pickle.load
            
            def safe_torch_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            
            def safe_pickle_load(*args, **kwargs):
                # pickle의 보안 설정 완화
                import pickle
                original_pickle_loads = pickle.loads
                def safe_loads(data):
                    return original_pickle_loads(data)
                pickle.loads = safe_loads
                try:
                    return original_pickle_load(*args, **kwargs)
                finally:
                    pickle.loads = original_pickle_loads
            
            torch.load = safe_torch_load
            pickle.load = safe_pickle_load
            
            # 모델 로드
            # weights_only=False로 모델 로딩
            original_load = torch.load
            torch.load = lambda *args, **kwargs: original_load(*args, **kwargs, weights_only=False)
            
            self.model = YOLO(self.model_path)
            
            # 원래 함수들 복원
            torch.load = original_load
            pickle.load = original_pickle_load
            
            print(f"✅ 세그멘테이션 모델 로드 완료: {self.model_path}")
            print(f"🔧 Device: {self.device}")
            
            # 원래 torch.load 복원
            torch.load = original_load
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            # 원래 함수들 복원 (오류 발생 시에도)
            try:
                torch.load = original_load
                pickle.load = original_pickle_load
            except:
                pass
            raise e
    
    def predict(self, image_input):
        """
        이미지에서 잎을 탐지하고 세그멘테이션 수행
        
        Args:
            image_input: PIL Image, numpy array, 또는 파일 경로
            
        Returns:
            dict: {
                'segmented_image': PIL Image,
                'cropped_leaves': list of PIL Images,
                'masks': list of numpy arrays,
                'boxes': list of bounding boxes
            }
        """
        try:
            # 이미지 전처리
            if isinstance(image_input, str):
                # 파일 경로인 경우
                image = Image.open(image_input)
            elif isinstance(image_input, np.ndarray):
                # numpy array인 경우
                image = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
            else:
                # PIL Image인 경우
                image = image_input
            
            # YOLO 모델로 예측
            results = self.model(image)
            
            # 결과 처리
            segmented_image, cropped_leaves, masks, boxes = self._process_results(image, results[0])
            
            return {
                'segmented_image': segmented_image,
                'cropped_leaves': cropped_leaves,
                'masks': masks,
                'boxes': boxes
            }
            
        except Exception as e:
            print(f"❌ 예측 실패: {e}")
            raise e
    
    def _process_results(self, original_image, result):
        """
        YOLO 결과를 처리하여 세그멘테이션된 이미지와 크롭된 잎들을 생성
        
        Args:
            original_image: 원본 PIL Image
            result: YOLO 결과 객체
            
        Returns:
            tuple: (segmented_image, cropped_leaves, masks, boxes)
        """
        # 원본 이미지를 numpy array로 변환
        img_array = np.array(original_image)
        height, width = img_array.shape[:2]
        
        # 세그멘테이션 마스크 초기화
        segmented_mask = np.zeros((height, width), dtype=np.uint8)
        
        cropped_leaves = []
        masks = []
        boxes = []
        
        if result.masks is not None:
            for i, mask in enumerate(result.masks.data):
                # 마스크를 원본 이미지 크기로 리사이즈
                mask_resized = cv2.resize(
                    mask.cpu().numpy(), 
                    (width, height), 
                    interpolation=cv2.INTER_NEAREST
                )
                
                # 마스크를 0-255 범위로 정규화
                mask_normalized = (mask_resized * 255).astype(np.uint8)
                masks.append(mask_normalized)
                
                # 전체 세그멘테이션 마스크에 추가
                segmented_mask = cv2.bitwise_or(segmented_mask, mask_normalized)
                
                # 바운딩 박스 계산
                contours, _ = cv2.findContours(mask_normalized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    x, y, w, h = cv2.boundingRect(contours[0])
                    boxes.append([x, y, x+w, y+h])
                    
                    # 잎 부분만 크롭
                    cropped_leaf = img_array[y:y+h, x:x+w]
                    if cropped_leaf.size > 0:
                        cropped_leaves.append(Image.fromarray(cropped_leaf))
        
        # 세그멘테이션된 이미지 생성 (원본 + 마스크 오버레이)
        segmented_image = self._create_segmented_image(img_array, segmented_mask)
        
        return segmented_image, cropped_leaves, masks, boxes
    
    def _create_segmented_image(self, original_img, mask):
        """
        원본 이미지에 세그멘테이션 마스크를 오버레이한 이미지 생성
        
        Args:
            original_img: 원본 이미지 (numpy array)
            mask: 세그멘테이션 마스크 (numpy array)
            
        Returns:
            PIL Image: 세그멘테이션된 이미지
        """
        # 컬러 마스크 생성 (녹색으로 잎 부분 표시)
        colored_mask = np.zeros_like(original_img)
        colored_mask[:, :, 1] = mask  # 녹색 채널에 마스크 적용
        
        # 원본 이미지와 마스크를 블렌딩
        alpha = 0.3  # 투명도
        segmented_img = cv2.addWeighted(original_img, 1-alpha, colored_mask, alpha, 0)
        
        return Image.fromarray(segmented_img)
    
    def save_cropped_leaves(self, cropped_leaves, output_dir="cropped_leaves"):
        """
        크롭된 잎 이미지들을 파일로 저장
        
        Args:
            cropped_leaves: 크롭된 잎 이미지 리스트
            output_dir: 저장할 디렉토리
            
        Returns:
            list: 저장된 파일 경로들
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        saved_paths = []
        for i, leaf_img in enumerate(cropped_leaves):
            filename = f"leaf_{i+1}.jpg"
            filepath = os.path.join(output_dir, filename)
            leaf_img.save(filepath, "JPEG", quality=95)
            saved_paths.append(filepath)
        
        return saved_paths
