# models/classifier/infer_classifier.py
import argparse
from pathlib import Path
import torch
from PIL import Image
from torchvision import transforms, models
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    EfficientNet_B0_Weights, EfficientNet_B2_Weights, EfficientNet_B3_Weights
)
import torch.nn as nn

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
    idx_to_class = {i:c for i,c in enumerate(classes)}
    return idx_to_class

def build_tfm(img_size):
    return transforms.Compose([
        transforms.Resize(int(img_size*1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize((0.485,0.456,0.406),(0.229,0.224,0.225)),
    ])

def predict_one(model, img_path: Path, tfm, device, idx_to_class, topk=3):
    img = Image.open(img_path).convert("RGB")
    x = tfm(img).unsqueeze(0).to(device)
    with torch.no_grad():
        prob = torch.softmax(model(x), dim=1)[0].cpu().numpy()
    top = prob.argsort()[-topk:][::-1]
    return [(idx_to_class[i], float(prob[i])) for i in top]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=str, required=True, help="models/weight/*.pth")
    ap.add_argument("--model",   type=str, required=True, help="학습 시 사용한 모델명")
    ap.add_argument("--image",   type=str, help="단일 이미지 경로")
    ap.add_argument("--dir",     type=str, help="이미지 폴더 경로(전체 추론)")
    ap.add_argument("--topk",    type=int, default=3)
    args = ap.parse_args()

    ckpt = torch.load(args.weights, map_location="cpu")
    idx_to_class = ckpt.get("classes")
    img_size = ckpt.get("img_size", 224)
    if idx_to_class is None:
        # fallback: labels.txt (학습 스크립트가 생성함)
        labels_path = Path(__file__).parent / "labels.txt"
        idx_to_class = load_labels(labels_path)

    model, rec = build_model(args.model, num_classes=len(idx_to_class))
    model.load_state_dict(ckpt["model"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()

    tfm = build_tfm(img_size if img_size else rec)

    targets = []
    if args.image:
        targets = [Path(args.image)]
    elif args.dir:
        p = Path(args.dir)
        targets = [p for p in p.iterdir() if p.suffix.lower() in [".jpg",".jpeg",".png",".bmp",".webp"]]
    else:
        raise ValueError("--image 또는 --dir 중 하나는 지정해야 합니다.")

    for img_path in targets:
        top = predict_one(model, img_path, tfm, device, idx_to_class, topk=args.topk)
        print(f"[{img_path.name}] -> {top}")

if __name__ == "__main__":
    main()
