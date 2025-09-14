# inference.py (입력채널 자동감지 + 5채널 전처리 + 안전한 경로)
import argparse, sys
from pathlib import Path

import torch
import torch.nn.functional as F
from timm import create_model
from torchvision import transforms as T
from PIL import Image
import torch.nn as nn
import torch.nn.functional as Fnn

# 유연 임포트 (패키지/직접 실행 모두 지원)
try:
    from pland_disease.NLG import generate_response
    from pland_disease.disease import DISEASE_INFO as disease_info
except ModuleNotFoundError:
    from NLG import generate_response
    from disease import DISEASE_INFO as disease_info

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
            x = x.unsqueeze(0)  # [1,3,H,W]
        r, g, b = x[:,0:1], x[:,1:2], x[:,2:3]
        gray = 0.2989*r + 0.5870*g + 0.1140*b
        gx = Fnn.conv2d(gray, self.kx, padding=1)
        gy = Fnn.conv2d(gray, self.ky, padding=1)
        sobel = torch.sqrt(gx*gx + gy*gy + 1e-8)
        lap   = Fnn.conv2d(gray, self.lap, padding=1).abs()

        def norm01(t):
            mn = t.amin(dim=(2,3), keepdim=True)
            mx = t.amax(dim=(2,3), keepdim=True)
            return (t - mn) / (mx - mn + 1e-8)

        sobel = norm01(sobel)
        lap   = norm01(lap)
        out = torch.cat([x, sobel, lap], dim=1)  # [1,5,H,W]
        return out.squeeze(0)

# ---------- 인자 ----------
ap = argparse.ArgumentParser()
ap.add_argument("--weights", type=str, default=None, help="path to best.pt (기본: 패키지 models/best.pt)")
ap.add_argument("--input", type=str, default="samples", help="이미지 파일 또는 폴더")
ap.add_argument("--topk", type=int, default=3)
ap.add_argument("--nickname", type=str, default="우리 식물")
ap.add_argument("--species", type=str, default="스투키")
args = ap.parse_args()

# ---------- 경로 ----------
PKG_DIR = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = PKG_DIR / "models" / "best.pt"
WEIGHTS = Path(args.weights) if args.weights else DEFAULT_WEIGHTS

if not WEIGHTS.exists():
    print(f"❌ 가중치 파일을 찾을 수 없습니다: {WEIGHTS.resolve()}")
    print("💡 예: python -m pland_disease.inference --weights models\\best.pt --input samples")
    sys.exit(1)

# ---------- 체크포인트 로드 ----------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ckpt = torch.load(str(WEIGHTS), map_location=device)
classes = ckpt["classes"]
cfg = ckpt.get("cfg", {})
MODEL_NAME = cfg.get("model", "efficientnet_b0")
IMG_SIZE   = cfg.get("img_size", 400)

# 입력 채널 자동 감지
state_dict = ckpt["model"]
conv_key = "conv_stem.weight"
if conv_key in state_dict:
    in_chans = int(state_dict[conv_key].shape[1])
else:
    in_chans = int(cfg.get("in_chans", 3))

# ---------- 모델 ----------
model = create_model(MODEL_NAME, pretrained=False, num_classes=len(classes), in_chans=in_chans)
model.load_state_dict(state_dict, strict=False)
model.to(device).eval()

# ---------- 전처리 ----------
MEAN_RGB, STD_RGB = (0.485,0.456,0.406), (0.229,0.224,0.225)
MEAN_5 = list(MEAN_RGB) + [0.5, 0.5]
STD_5  = list(STD_RGB)  + [0.5, 0.5]

if in_chans == 5:
    preprocess = T.Compose([
        T.Resize(IMG_SIZE),
        T.CenterCrop(IMG_SIZE),
        T.ToTensor(),
        AddTextureChannels(),
        T.Normalize(MEAN_5, STD_5),
    ])
else:
    preprocess = T.Compose([
        T.Resize(IMG_SIZE),
        T.CenterCrop(IMG_SIZE),
        T.ToTensor(),
        T.Normalize(MEAN_RGB, STD_RGB),
    ])

# ---------- 유틸 ----------
def list_images(path: Path):
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    p = Path(path)
    if p.is_file() and p.suffix.lower() in exts:
        return [p]
    if p.is_dir():
        return sorted([x for x in p.rglob("*") if x.suffix.lower() in exts])
    return []

# ---------- 추론 ----------
@torch.no_grad()
def predict(img_path: Path, plant_nickname: str, plant_species: str, topk: int = 3):
    img = Image.open(img_path).convert("RGB")
    x = preprocess(img).unsqueeze(0).to(device)

    logits = model(x)
    probs = torch.softmax(logits, dim=1)[0]
    top_p, top_c = probs.topk(topk)
    preds = [(classes[int(i)], float(p)) for p, i in zip(top_p.tolist(), top_c.tolist())]

    # NLG
    response = generate_response(plant_nickname, plant_species, preds)

    # 로그
    print(f"\n📷 {img_path.name}")
    for rank, (label, _) in enumerate(preds, start=1):
        print(f" - {rank}순위: {label}")
    print("💬", response)

    return preds, response

# ---------- main ----------
def main():
    src = Path(args.input)
    imgs = list_images(src)
    if not imgs:
        print("❌ 입력 경로에서 이미지를 찾지 못했습니다:", src.resolve())
        sys.exit(1)
    for p in imgs:
        predict(p, args.nickname, args.species, args.topk)

if __name__ == "__main__":
    main()
