# 간단 설명:
# - 처음 호출될 때만 가중치/모델/전처리 로딩(지연 로딩)
# - predict_path / predict_image 2개 함수만 공개
# - 네 inference.py와 동등한 전처리(3/5채널 자동), NLG 연동 유지

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Union
import os, threading

import torch
from timm import create_model
from torchvision import transforms as T
from PIL import Image
import torch.nn as nn
import torch.nn.functional as F


from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 유연 임포트 (패키지/단독 모두)
try:
    from .NLG import generate_response
    from .disease import DISEASE_INFO as disease_info
except ImportError:
    try:
        from NLG import generate_response
        from disease import DISEASE_INFO as disease_info
    except ImportError:
        # NLG 모듈이 없는 경우 더미 함수 사용
        def generate_response(nickname, species, preds):
            if preds and len(preds) > 0:
                top_pred = preds[0]
                return f"식물 '{nickname}' ({species})에서 '{top_pred[0]}' 병충해가 감지되었습니다. (신뢰도: {top_pred[1]:.2f})"
            return f"식물 '{nickname}' ({species})의 병충해 분석이 완료되었습니다."
        
        # disease 모듈이 없는 경우 더미 데이터 사용
        disease_info = {
            "unknown": {
                "description": "알 수 없는 병충해",
                "treatment": "식물 전문가에게 상담하세요.",
                "prevention": "정기적인 관찰과 관리가 필요합니다."
            }
        }

    

# ===== 설정(환경변수로 덮어쓰기 가능) =====
MODEL_PATH = os.getenv("PLANT_MODEL")
DEVICE     = os.getenv("PLANT_DEVICE", "cuda" if torch.cuda.is_available() else "cpu").strip()

# ===== 전역 상태(지연 로딩) =====
_model = None
_classes: List[str] | None = None
_preprocess: T.Compose | None = None
_img_size: int | None = None
_in_chans: int | None = None
_lock = threading.Lock()

# ---------- 5채널 전처리 ----------
class AddTextureChannels(nn.Module):
    """RGB [3,H,W] -> [5,H,W]: RGB + SobelMag + Laplacian (0~1 정규화)"""
    def __init__(self):
        super().__init__()
        kx  = torch.tensor([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=torch.float32).view(1,1,3,3)
        ky  = torch.tensor([[-1,-2,-1],[0,0,0],[1,2,1]], dtype=torch.float32).view(1,1,3,3)
        lap = torch.tensor([[0,-1,0],[-1,4,-1],[0,-1,0]], dtype=torch.float32).view(1,1,3,3)
        self.register_buffer("kx", kx); self.register_buffer("ky", ky); self.register_buffer("lap", lap)

    def forward(self, x):  # x: [C,H,W] in [0,1]
        if x.dim() == 3:
            x = x.unsqueeze(0)
        r, g, b = x[:,0:1], x[:,1:2], x[:,2:3]
        gray = 0.2989*r + 0.5870*g + 0.1140*b
        gx = F.conv2d(gray, self.kx, padding=1)
        gy = F.conv2d(gray, self.ky, padding=1)
        sobel = torch.sqrt(gx*gx + gy*gy + 1e-8)
        lap   = F.conv2d(gray, self.lap, padding=1).abs()

        def norm01(t):
            mn = t.amin(dim=(2,3), keepdim=True)
            mx = t.amax(dim=(2,3), keepdim=True)
            return (t - mn) / (mx - mn + 1e-8)

        sobel = norm01(sobel); lap = norm01(lap)
        out = torch.cat([x, sobel, lap], dim=1)
        return out.squeeze(0)

def _build_preprocess(img_size: int, in_chans: int):
    MEAN_RGB, STD_RGB = (0.485,0.456,0.406), (0.229,0.224,0.225)
    if in_chans == 5:
        mean = list(MEAN_RGB) + [0.5, 0.5]
        std  = list(STD_RGB)  + [0.5, 0.5]
        return T.Compose([T.Resize(img_size), T.CenterCrop(img_size), T.ToTensor(),
                          AddTextureChannels(), T.Normalize(mean, std)])
    else:
        return T.Compose([T.Resize(img_size), T.CenterCrop(img_size), T.ToTensor(),
                          T.Normalize(MEAN_RGB, STD_RGB)])

def _load_once():
    """체크포인트를 읽어 모델/전처리/클래스를 한 번만 구성"""
    global _model, _classes, _preprocess, _img_size, _in_chans
    if _model is not None:
        return
    with _lock:
        if _model is not None:
            return
        device = torch.device(DEVICE)
        ckpt = torch.load(str(MODEL_PATH), map_location=device)  # {"classes","model","cfg"}
        _classes = ckpt["classes"]
        state_dict = ckpt["model"]
        cfg = ckpt.get("cfg", {})
        model_name = cfg.get("model", "efficientnet_b0")
        _img_size  = int(cfg.get("img_size", 400))

        # 입력 채널 자동 감지
        if "conv_stem.weight" in state_dict:
            _in_chans = int(state_dict["conv_stem.weight"].shape[1])
        else:
            _in_chans = int(cfg.get("in_chans", 3))

        m = create_model(model_name, pretrained=False, num_classes=len(_classes), in_chans=_in_chans)
        m.load_state_dict(state_dict, strict=False)
        _model = m.to(device).eval()
        _preprocess = _build_preprocess(_img_size, _in_chans)

@torch.no_grad()
def predict_image(img: Image.Image, topk: int = 3,
                  nickname: str = "우리 식물", species: str = "스투키"):
    """PIL.Image -> (preds, nlg_message)"""
    _load_once()
    x = _preprocess(img.convert("RGB")).unsqueeze(0).to(DEVICE)
    logits = _model(x)
    probs  = torch.softmax(logits, dim=1)[0].cpu()
    p, i   = probs.topk(topk)
    preds: List[Tuple[str, float]] = [(_classes[int(k)], float(v)) for v,k in zip(p.tolist(), i.tolist())]
    msg = generate_response(nickname, species, preds)
    return preds, msg

def predict_path(path: Union[str, Path], **kw):
    """파일 경로 입력 버전"""
    return predict_image(Image.open(path), **kw)
