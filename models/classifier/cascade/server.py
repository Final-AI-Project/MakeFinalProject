# server.py  — D:\hwan\AIFinalProject\models\classifier\cascade
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    EfficientNet_B0_Weights, EfficientNet_B2_Weights, EfficientNet_B3_Weights
)

# ===== 기존 infer_classifier.py 와 동일한 유틸 일부 재사용 =====

def build_model(model_name: str, num_classes: int):
    name = model_name.lower()
    if name in ["mobilenet", "mobilenet_v3_large"]:
        m = models.mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b0","effnet_b0"]:
        m = models.efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b2","effnet_b2"]:
        m = models.efficientnet_b2(weights=EfficientNet_B2_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 260
    elif name in ["efficientnet_b3","effnet_b3"]:
        m = models.efficientnet_b3(weights=EfficientNet_B3_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 300
    else:
        raise ValueError("지원하지 않는 모델명")
    return m, rec

def load_labels(labels_path: Path):
    with open(labels_path, "r", encoding="utf-8") as f:
        classes = [line.strip() for line in f if line.strip()]
    idx_to_class = {i: c for i, c in enumerate(classes)}
    return idx_to_class

def build_tfm(img_size):
    return transforms.Compose([
        transforms.Resize(int(img_size * 1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize((0.485,0.456,0.406),(0.229,0.224,0.225)),
    ])

# ===== 한글 라벨 매핑(있으면 변환) =====
CLASS_KOR = {
    "mon": "몬스테라",
    "stk": "스투키",
    "zz":  "금전수",
    "cac": "선인장/다육",
    "pha": "호접란",
    "cha": "테이블야자",
    "sch": "홍콩야자",
    "spa": "스파티필럼",
    "lad": "관음죽",
    "fic": "벵갈고무나무",
    "oli": "올리브나무",
    "die": "디펜바키아",
    "bos": "보스턴고사리",
}

# ===== 앱/모델 준비 =====
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

ROOT = Path(__file__).parent
WEIGHTS = ROOT / "weight" / "mobilenet_v3_large_best.pth"
LABELS  = ROOT / "labels.txt"
MODEL_NAME = "mobilenet_v3_large"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1) 클래스/모델/변환 로딩 (서버 시작 시 1회)
ckpt = torch.load(WEIGHTS, map_location="cpu")
idx_to_class = ckpt.get("classes")
if idx_to_class is None:
    idx_to_class = load_labels(LABELS)

model, rec = build_model(MODEL_NAME, num_classes=len(idx_to_class))
model.load_state_dict(ckpt["model"])
model = model.to(device).eval()
img_size = ckpt.get("img_size", rec)
tfm = build_tfm(img_size)

@app.get("/healthcheck")
def health():
    return {"ok": True, "device": str(device)}

@app.post("/plants/classify-species")
async def classify_species(image: UploadFile = File(...)):
    # 메모리에서 바로 처리 (파일 저장 X)
    data = await image.read()
    try:
        img = Image.open(BytesIO(data)).convert("RGB")
    except Exception as e:
        return {"success": False, "error": f"이미지 열기 실패: {e}"}

    x = tfm(img).unsqueeze(0).to(device)
    with torch.no_grad():
        prob = torch.softmax(model(x), dim=1)[0].cpu().numpy()

    top_idx = prob.argmax()
    label = idx_to_class[top_idx]
    species = CLASS_KOR.get(label, label)
    conf = float(prob[top_idx])  # 0~1

    # 옵션: 상위 3개 함께 보내기
    topk = prob.argsort()[-3:][::-1]
    top = [
        [CLASS_KOR.get(idx_to_class[i], idx_to_class[i]), float(prob[i])]
        for i in topk
    ]

    return {
        "success": True,
        "species": species,
        "confidence": round(conf * 100, 2),  # %로 반환
        "top": top,  # 각 항목 확률은 0~1
    }
