from ultralytics import YOLO
from ultralytics import settings
from PIL import Image
import numpy as np
import dotenv
import torch

# === PyTorch 2.6 호환성을 위한 설정 ===
# torch.load의 weights_only를 False로 설정
torch.serialization.DEFAULT_PROTOCOL = 2

# 전역적으로 torch.load 설정
import torch
original_torch_load = torch.load
def safe_torch_load(*args, **kwargs):
    # weights_only가 이미 있으면 제거하고 False로 설정
    kwargs.pop('weights_only', None)
    kwargs['weights_only'] = False
    return original_torch_load(*args, **kwargs)
torch.load = safe_torch_load

# === 모델은 전역으로 1회만 로드 ===
MODEL_PATH = "healthy/healthy.pt"
IMG_SIZE = 224  # 학습 때 사용한 imgsz
DEVICE = "cpu"  # "cuda" 가능하면 "cuda"

# 모델 로딩을 지연시키기 위해 None으로 초기화
model = None
names = None

def _load_model():
    """모델을 지연 로딩하는 함수"""
    global model, names
    if model is None:
        # 전역 torch.load 설정이 이미 적용되어 있음
        model = YOLO(MODEL_PATH)
        if DEVICE:
            model.to(DEVICE)
        names = model.names

def predict_image(img: Image.Image, topk: int = 5):
    _load_model()  # 필요할 때 모델 로딩
    
    res = model.predict(img, imgsz=IMG_SIZE, verbose=False)[0]
    probs = res.probs.data.cpu().numpy()
    idxs = np.argsort(-probs)[:topk]

    results = [
        {"class_id": int(i), "class_name": names[int(i)], "score": float(probs[i])}
        for i in idxs
    ]
    return {"class_name": results[0]["class_name"], "score": results[0]["score"]}
