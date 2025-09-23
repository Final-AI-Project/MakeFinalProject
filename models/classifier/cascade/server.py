# server.py
# 실행: uvicorn server:app --host 0.0.0.0 --port 4000

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
import importlib.util

# ────────────────────────────────────────────────
# 경로 설정
HERE = Path(__file__).resolve().parent                           # .../models/classifier/cascade
CASCADE_DIR = HERE
WEIGHT_PATH = CASCADE_DIR / "weight" / "mobilenet_v3_large_best.pth"
LABELS_PATH = CASCADE_DIR / "labels.txt"

# 라벨 로드
labels = [ln.strip() for ln in open(LABELS_PATH, encoding="utf-8").read().splitlines() if ln.strip()]
NUM_CLASSES = len(labels)

# ────────────────────────────────────────────────
# 유틸: 커스텀 빌더가 튜플/리스트를 반환해도 nn.Module만 추출
def ensure_module(x):
    if isinstance(x, nn.Module):
        return x
    if isinstance(x, (list, tuple)):
        for item in x:
            if isinstance(item, nn.Module):
                return item
    raise TypeError(f"Custom builder returned non-module: {type(x)}")

# 커스텀 빌더 시도
def try_build_custom(num_classes: int, model_name: str = "mobilenet_v3_large") -> Optional[nn.Module]:
    infer_py = CASCADE_DIR / "infer_classifier.py"
    if not infer_py.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("infer_classifier", str(infer_py))
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        for cand in ["build_model", "build_classifier", "create_model"]:
            fn = getattr(mod, cand, None)
            if not callable(fn):
                continue
            print(f"[INFO] try custom builder: {cand}(model_name='{model_name}', num_classes={num_classes})")
            # 다양한 시그니처 시도
            try:
                m = fn(model_name=model_name, num_classes=num_classes)  # kw 시도
                print("[INFO] using custom builder: build_model (kw ok)")
                return ensure_module(m)
            except TypeError:
                pass
            try:
                m = fn(model_name, num_classes)  # 위치 인자 시도
                print("[INFO] using custom builder: build_model (pos ok)")
                return ensure_module(m)
            except TypeError:
                pass
            try:
                m = fn(num_classes=num_classes)  # num_classes만
                print("[INFO] using custom builder: build_model (num_classes only)")
                return ensure_module(m)
            except TypeError:
                continue
        print("[WARN] no valid builder signature in infer_classifier.py")
        return None
    except Exception as e:
        print(f"[WARN] custom builder import failed: {e}")
        return None

# torchvision 백업
def build_torchvision_mbv3(num_classes: int) -> nn.Module:
    from torchvision.models import mobilenet_v3_large
    m = mobilenet_v3_large(weights=None)
    if isinstance(m.classifier, nn.Sequential) and isinstance(m.classifier[-1], nn.Linear):
        in_f = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_f, num_classes)
    else:
        last_lin = None
        for mod in reversed(list(m.classifier.modules())):
            if isinstance(mod, nn.Linear):
                last_lin = mod; break
        if last_lin is None:
            raise RuntimeError("cannot locate final Linear in classifier")
        in_f = last_lin.in_features
        m.classifier = nn.Sequential(nn.Linear(in_f, num_classes))
    print("[INFO] torchvision mobilenet_v3_large built")
    return m

# 가중치 로드
def load_weights(model: nn.Module, weights_path: Path):
    ckpt = torch.load(str(weights_path), map_location="cpu")
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        sd = ckpt["state_dict"]
    elif isinstance(ckpt, dict):
        # 일부 체크포인트는 {"model": state_dict, ...}
        sd = ckpt.get("model", ckpt)
    else:
        try:
            model.load_state_dict(ckpt.state_dict())
            print("[INFO] loaded from full model object")
            return
        except Exception as e:
            raise RuntimeError(f"unknown checkpoint format: {type(ckpt)} {e}")

    # module. prefix 제거
    sd = { (k[7:] if k.startswith("module.") else k): v for k, v in sd.items() }
    try:
        model.load_state_dict(sd, strict=True)
        print("[INFO] state_dict strict=True loaded")
    except Exception as e:
        print(f"[WARN] strict=True failed: {e}")
        model.load_state_dict(sd, strict=False)
        print("[INFO] state_dict strict=False loaded")

# ────────────────────────────────────────────────
# 모델 준비 (앱 시작 시 1회)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] device={device}")

model = try_build_custom(NUM_CLASSES, model_name="mobilenet_v3_large") or build_torchvision_mbv3(NUM_CLASSES)
model = ensure_module(model)  # ★ 커스텀 빌더가 튜플을 반환해도 안전
load_weights(model, WEIGHT_PATH)
model.to(device).eval()

# 전처리 (224x224, ImageNet mean/std)
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# ────────────────────────────────────────────────
# FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthcheck")
async def healthcheck():
    return {
        "ok": True,
        "device": str(device),
        "classes": NUM_CLASSES,
        "labels_head": labels[:5],
    }

@app.post("/plants/classify-species")
async def classify_species(image: UploadFile = File(...)):
    try:
        img = Image.open(image.file).convert("RGB")
        x = transform(img).unsqueeze(0).to(device)  # [1,3,224,224]
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)[0]
        conf, idx = torch.max(probs, dim=0)
        species = labels[idx.item()]
        confidence = round(conf.item() * 100, 2)
        return {"success": True, "species": species, "confidence": confidence}
    except Exception as e:
        return {"success": False, "error": str(e)}
