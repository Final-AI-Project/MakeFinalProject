# YOLOv8-Seg 잎 탐지 모델 유틸리티

YOLOv8-Segmentation 모델을 사용한 식물 잎 탐지 유틸리티입니다.

## 📁 프로젝트 구조

```
YOLO8s-seg/
├── README.md              # 이 파일
├── requirements.txt       # Python 의존성
└── yolo_seg_utils.py     # 모델 로딩/추론/후처리
```

## 🚀 설치

```bash
pip install -r requirements.txt
```

## 📖 사용법

### 1. 모델 로드

```python
from yolo_seg_utils import load_yolo_seg_model

# 모델 로드
model = load_yolo_seg_model("path/to/your/best.pt", device="0")
```

### 2. 이미지 추론

```python
import cv2
from yolo_seg_utils import infer_image, preprocess_image

# 이미지 로드
image = cv2.imread("leaf_image.jpg")

# 추론 수행
detections = infer_image(model, image)

# 결과 확인
for detection in detections:
    print(f"클래스: {detection['cls']}")
    print(f"신뢰도: {detection['conf']:.3f}")
    print(f"바운딩 박스: {detection['bbox_xyxy']}")
    print(f"폴리곤: {detection['polygon']}")
```

### 3. 바이트 데이터 처리

```python
from yolo_seg_utils import preprocess_image, infer_image

# 바이트 데이터에서 이미지 추론
with open("image.jpg", "rb") as f:
    image_bytes = f.read()

# 전처리
image = preprocess_image(image_bytes)

# 추론
detections = infer_image(model, image)
```

## 🔧 설정

`yolo_seg_utils.py`에서 다음 설정을 수정할 수 있습니다:

```python
# 기본 설정
DEFAULT_MODEL_PATH = "path/to/your/best.pt"  # 모델 경로
DEFAULT_DEVICE = "0"                         # GPU: "0", CPU: "cpu"
DEFAULT_IMG_SIZE = 640                       # 입력 이미지 크기
DEFAULT_CONF_THRES = 0.25                    # 신뢰도 임계값
DEFAULT_IOU_THRES = 0.45                     # NMS IoU 임계값
DEFAULT_MAX_DET = 100                        # 최대 탐지 개수
```

## 📊 응답 형식

```python
{
    "cls": 0,                    # 클래스 ID
    "conf": 0.91,                # 신뢰도 (0.0 ~ 1.0)
    "bbox_xyxy": [234, 120, 480, 420],  # 바운딩 박스 [x1, y1, x2, y2]
    "polygon": [[240, 130], [260, 128], ...]  # 폴리곤 좌표 리스트
}
```

## 🐛 오류 처리

- `FileNotFoundError`: 모델 파일이 존재하지 않을 때
- `Exception`: 모델 로딩 또는 추론 실패 시
- 이미지 디코딩 실패 시 `None` 반환

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
