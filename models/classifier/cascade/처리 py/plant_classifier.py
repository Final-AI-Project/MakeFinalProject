# models/classifier/plant_classifier.py
import argparse, random, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import datasets, transforms, models
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    EfficientNet_B0_Weights
)

# -----------------------------
# 프로젝트 기본 설정
# -----------------------------
CLASSES = [
    "monstera","stuckyi_sansevieria","zz_plant","cactus_succulent","phalaenopsis",
    "chamaedorea","schefflera","spathiphyllum","lady_palm","ficus_audrey",
    "olive_tree","dieffenbachia","boston_fern"
]

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)

# -----------------------------
# 더미 이미지 생성기
# -----------------------------
def make_dummy_image(w=256, h=256):
    # 노이즈 + 퍼린풍 질감 흉내 (간단 버전)
    arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

    # 간단한 “잎맥” 같은 선형 패턴 몇 개 추가
    img = Image.fromarray(arr, mode="RGB")
    drw = ImageDraw.Draw(img)
    for _ in range(random.randint(5, 12)):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)
        thickness = random.randint(1, 3)
        drw.line((x1, y1, x2, y2), fill=(random.randint(0,255),random.randint(50,255),random.randint(0,255)), width=thickness)
    # 약간 블러로 부드럽게
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.0, 1.2)))
    return img

def bootstrap_dummy_dataset(root: Path, n_train=30, n_val=10, img_size=256):
    train_dir = root / "train"
    val_dir   = root / "val"
    for split_dir, n in [(train_dir, n_train), (val_dir, n_val)]:
        for cls in CLASSES:
            (split_dir/cls).mkdir(parents=True, exist_ok=True)
            # 한 클래스마다 n장 생성
            for i in range(n):
                img = make_dummy_image(img_size, img_size)
                img.save(split_dir/cls/f"dummy_{i:03d}.jpg", quality=85)

# -----------------------------
# 데이터로더/증강
# -----------------------------
def make_loaders(data_root: Path, img_size=224, batch=32, workers=2, weighted_sampler=True):
    mean=(0.485,0.456,0.406); std=(0.229,0.224,0.225)
    train_tfms = transforms.Compose([
        transforms.RandomResizedCrop(img_size, scale=(0.7,1.0)),
        transforms.RandomHorizontalFlip(0.5),
        transforms.ColorJitter(0.2,0.2,0.2,0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    val_tfms = transforms.Compose([
        transforms.Resize(int(img_size*1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    train_ds = datasets.ImageFolder(str(data_root/"train"), transform=train_tfms)
    val_ds   = datasets.ImageFolder(str(data_root/"val"),   transform=val_tfms)

    if weighted_sampler:
        counts = np.bincount([y for _, y in train_ds.samples])
        weights = 1.0 / np.clip(counts, 1, None)
        sample_w = [weights[y] for _, y in train_ds.samples]
        sampler = WeightedRandomSampler(sample_w, num_samples=len(sample_w), replacement=True)
        train_loader = DataLoader(train_ds, batch_size=batch, sampler=sampler, num_workers=workers, pin_memory=True)
    else:
        train_loader = DataLoader(train_ds, batch_size=batch, shuffle=True, num_workers=workers, pin_memory=True)

    val_loader = DataLoader(val_ds, batch_size=batch, shuffle=False, num_workers=workers, pin_memory=True)
    return train_ds, val_ds, train_loader, val_loader

# -----------------------------
# 모델
# -----------------------------
def build_model(model_name: str, num_classes: int):
    name = model_name.lower()
    if name in ["mobilenet","mobilenet_v3_large"]:
        m = models.mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b0","effnet_b0","efficientnet"]:
        m = models.efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    else:
        raise ValueError("지원 모델: mobilenet_v3_large | efficientnet_b0")
    return m, rec

# -----------------------------
# 학습 루프(라이트)
# -----------------------------
def train(model, train_loader, val_loader, device, epochs=5, lr=3e-4):
    crit = nn.CrossEntropyLoss()
    opt  = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sch  = CosineAnnealingLR(opt, T_max=epochs)

    best_w = model.state_dict()
    best_acc = 0.0
    for ep in range(1, epochs+1):
        # train
        model.train()
        tr_loss=0.0; tr_hit=0; n=0
        for x,y in train_loader:
            x,y = x.to(device), y.to(device)
            opt.zero_grad()
            logit = model(x)
            loss  = crit(logit, y)
            loss.backward(); opt.step()
            tr_loss += loss.item()*x.size(0)
            tr_hit  += (logit.argmax(1)==y).sum().item()
            n += x.size(0)
        # val
        model.eval()
        va_loss=0.0; va_hit=0; m=0
        with torch.no_grad():
            for x,y in val_loader:
                x,y = x.to(device), y.to(device)
                logit = model(x)
                loss  = crit(logit, y)
                va_loss += loss.item()*x.size(0)
                va_hit  += (logit.argmax(1)==y).sum().item()
                m += x.size(0)
        tr_acc = tr_hit/max(n,1); va_acc = va_hit/max(m,1)
        print(f"[{ep:02d}/{epochs}] train_loss={tr_loss/n:.4f} acc={tr_acc:.3f} | val_loss={va_loss/m:.4f} acc={va_acc:.3f}")
        if va_acc > best_acc:
            best_acc = va_acc
            best_w = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        sch.step()
    model.load_state_dict(best_w)
    print(f"Best Val Acc (dummy): {best_acc:.4f}")
    return model

# -----------------------------
# main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_root", type=str, default="plants-dataset", help="train/val 포함 루트")
    ap.add_argument("--model", type=str, default="efficientnet_b0",
                    choices=["mobilenet_v3_large","efficientnet_b0","mobilenet","efficientnet"])
    ap.add_argument("--epochs", type=int, default=5, help="더미 학습은 짧게")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--force_bootstrap", action="store_true", help="데이터 있어도 강제 더미 생성")
    args = ap.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    data_root = Path(args.data_root)
    train_dir = data_root / "train"
    val_dir   = data_root / "val"

    # 1) 데이터셋 없으면 더미 생성
    need_bootstrap = args.force_bootstrap or (not train_dir.exists()) or (not val_dir.exists())
    if need_bootstrap:
        print("[INFO] dataset not found → bootstrap dummy dataset...")
        bootstrap_dummy_dataset(data_root, n_train=30, n_val=10, img_size=256)
    else:
        # 폴더가 비어있으면 역시 부트스트랩
        has_any = any((train_dir/glob).exists() and any((train_dir/glob).iterdir()) for glob in CLASSES)
        if not has_any:
            print("[INFO] empty dataset → bootstrap dummy dataset...")
            bootstrap_dummy_dataset(data_root, n_train=30, n_val=10, img_size=256)

    # 2) 로더
    train_ds, val_ds, train_loader, val_loader = make_loaders(data_root, img_size=224,
                                                              batch=args.batch, workers=2, weighted_sampler=True)
    num_classes = len(train_ds.classes)
    print("Classes:", train_ds.classes)

    # 3) 모델
    model, rec = build_model(args.model, num_classes)
    model = model.to(device)

    # 4) 라이트 학습
    model = train(model, train_loader, val_loader, device, epochs=args.epochs, lr=3e-4)

    # 5) 저장 (더미 전용 가중치)
    weight_dir = Path(__file__).resolve().parents[1] / "weight"
    weight_dir.mkdir(parents=True, exist_ok=True)
    save_path = weight_dir / f"{args.model}_dummy_best.pth"
    torch.save({"model": model.state_dict(),
                "classes": {i:c for i,c in enumerate(train_ds.classes)},
                "img_size": 224}, save_path)
    print("Saved dummy weight ->", save_path)
    print("\n[NOTE] 이 가중치는 더미 데이터로 학습된 것이며, 실제 식물 분류 용도로 사용하면 안 됩니다.")

if __name__ == "__main__":
    main()
