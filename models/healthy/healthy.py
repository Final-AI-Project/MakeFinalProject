from ultralytics import YOLO
from ultralytics import settings
from PIL import Image
import numpy as np
import dotenv

# === 모델은 전역으로 1회만 로드 ===
MODEL_PATH = "healthy/healthy.pt"
IMG_SIZE = 224  # 학습 때 사용한 imgsz
DEVICE = "cpu"  # "cuda" 가능하면 "cuda"

model = YOLO(MODEL_PATH)
if DEVICE:
    model.to(DEVICE)

names = model.names  # 클래스 이름

def predict_image(img: Image.Image, topk: int = 5):
    res = model.predict(img, imgsz=IMG_SIZE, verbose=False)[0]
    probs = res.probs.data.cpu().numpy()
    idxs = np.argsort(-probs)[:topk]

    results = [
        {"class_id": int(i), "class_name": names[int(i)], "score": float(probs[i])}
        for i in idxs
    ]
    return {"class_name": results[0]["class_name"], "score": results[0]["score"]}
