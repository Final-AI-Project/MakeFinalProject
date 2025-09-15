# models/classifier/cascade/cascade.py
# Python 3.11 / Tab size 4

import argparse, copy, random, re
from pathlib import Path
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import datasets, transforms, models
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    EfficientNet_B0_Weights, EfficientNet_B2_Weights, EfficientNet_B3_Weights
)

# ----------------------------- 
# utils
# -----------------------------
def set_seed(seed=42):
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)

def build_model(model_name: str, num_classes: int, img_size: int):
    name = model_name.lower()
    if name in ["mobilenet", "mobilenet_v3_large"]:
        weights = MobileNet_V3_Large_Weights.IMAGENET1K_V2
        model = models.mobilenet_v3_large(weights=weights)
        in_feat = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b0", "effnet_b0"]:
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=weights)
        in_feat = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b2", "effnet_b2"]:
        weights = EfficientNet_B2_Weights.IMAGENET1K_V1
        model = models.efficientnet_b2(weights=weights)
        in_feat = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 260
    elif name in ["efficientnet_b3", "effnet_b3"]:
        weights = EfficientNet_B3_Weights.IMAGENET1K_V1
        model = models.efficientnet_b3(weights=weights)
        in_feat = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 300
    else:
        raise ValueError("지원하지 않는 모델명")

    if img_size <= 0:
        img_size = rec
    elif img_size != rec:
        print(f"[주의] {model_name} 권장 입력 {rec}, 현재 {img_size}. 가능은 하지만 권장값 사용을 추천합니다.")
    return model, img_size

def make_loaders(train_dir: Path, val_dir: Path, img_size: int, batch_size: int,
                 num_workers: int, weighted_sampler: bool):
    mean=(0.485,0.456,0.406); std=(0.229,0.224,0.225)

    train_tfms = transforms.Compose([
        transforms.RandomResizedCrop(img_size, scale=(0.7,1.0)),
        transforms.RandomHorizontalFlip(0.5),
        transforms.ColorJitter(0.2,0.2,0.2,0.1),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    val_tfms = transforms.Compose([
        transforms.Resize(int(img_size*1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    train_ds = datasets.ImageFolder(str(train_dir), transform=train_tfms)
    val_ds   = datasets.ImageFolder(str(val_dir),   transform=val_tfms)

    if weighted_sampler:
        counts = np.bincount([y for _, y in train_ds.samples])
        weights = 1.0 / np.clip(counts, 1, None)
        sample_w = [weights[y] for _, y in train_ds.samples]
        sampler = WeightedRandomSampler(sample_w, num_samples=len(sample_w), replacement=True)
        train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler,
                                  num_workers=num_workers, pin_memory=True)
    else:
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                                  num_workers=num_workers, pin_memory=True)

    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=num_workers, pin_memory=True)

    return train_ds, val_ds, train_loader, val_loader

# --- 추가: 연속 에폭 저장을 위한 시작 에폭 탐지 ---
def find_start_epoch(weight_dir: Path, model_name: str) -> int:
    """
    models/weight/ 아래에 이미 저장된 {model_name}_epoch{N}.pth 파일을 스캔하여
    가장 큰 N을 반환. 없으면 0.
    """
    pattern = re.compile(rf"^{re.escape(model_name)}_epoch(\d+)\.pth$")
    max_ep = 0
    if weight_dir.exists():
        for f in weight_dir.iterdir():
            if f.is_file():
                m = pattern.match(f.name)
                if m:
                    n = int(m.group(1))
                    if n > max_ep:
                        max_ep = n
    return max_ep

def train(model, train_loader, val_loader, device, epochs=20, lr=3e-4,
          weight_dir: Path = None, model_name: str = None, start_epoch_offset: int = 0):
    crit = nn.CrossEntropyLoss()
    opt  = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sch  = CosineAnnealingLR(opt, T_max=epochs)

    best_w = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for ep in range(1, epochs+1):
        model.train()
        tr_loss=0.0; tr_hit=0; n=0
        for x,y in train_loader:
            x,y = x.to(device), y.to(device)
            opt.zero_grad()
            logit = model(x)
            loss = crit(logit, y)
            loss.backward()
            opt.step()

            tr_loss += loss.item()*x.size(0)
            tr_hit  += (logit.argmax(1)==y).sum().item()
            n += x.size(0)

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

        tr_acc = tr_hit/max(n,1)
        va_acc = va_hit/max(m,1)
        print(f"[{ep:02d}/{epochs}] train_loss={tr_loss/n:.4f} acc={tr_acc:.3f} | val_loss={va_loss/m:.4f} acc={va_acc:.3f}")

        if va_acc > best_acc:
            best_acc = va_acc
            best_w = copy.deepcopy(model.state_dict())

        # --- 추가: 에폭별 가중치 연속 저장 ---
        if weight_dir is not None and model_name is not None:
            global_epoch = start_epoch_offset + ep  # 이전 실행까지 누적 + 이번 실행의 ep(1~epochs)
            weight_dir.mkdir(parents=True, exist_ok=True)
            epoch_path = weight_dir / f"{model_name}_epoch{global_epoch}.pth"
            torch.save({
                "model": model.state_dict(),
                "epoch": global_epoch,
                "train_loss": tr_loss / max(n, 1),
                "train_acc": tr_acc,
                "val_loss": va_loss / max(m, 1),
                "val_acc": va_acc,
            }, epoch_path)
            print(f"Saved epoch weight -> {epoch_path}")

        sch.step()

    model.load_state_dict(best_w)
    print(f"Best Val Acc: {best_acc:.4f}")
    return model, best_acc

# -----------------------------
# main
# -----------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data_root", type=str, default="plants-dataset", help="train/val 포함 루트")
    p.add_argument("--model", type=str, default="efficientnet_b0",
                   choices=["mobilenet_v3_large","efficientnet_b0","efficientnet_b2","efficientnet_b3","mobilenet","effnet_b0","effnet_b2","effnet_b3"])
    p.add_argument("--img_size", type=int, default=0, help="0이면 모델 권장 크기 사용")
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--weighted_sampler", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    data_root = Path(args.data_root)
    train_dir = data_root / "train"
    val_dir   = data_root / "val"
    assert train_dir.exists() and val_dir.exists(), "plants-dataset/train, val 구조를 준비하세요."

    # 데이터/라벨
    train_ds, val_ds, train_loader, val_loader = make_loaders(
        train_dir, val_dir, args.img_size if args.img_size>0 else 224,
        args.batch, args.workers, args.weighted_sampler
    )
    num_classes = len(train_ds.classes)
    idx_to_class = {v:k for k,v in train_ds.class_to_idx.items()}
    labels_txt = Path(__file__).parent / "labels.txt"   # models/classifier/cascade/labels.txt
    with open(labels_txt, "w", encoding="utf-8") as f:
        for i in range(num_classes):
            f.write(idx_to_class[i] + "\n")
    print("Saved labels ->", labels_txt)

    # 모델
    model, img_size = build_model(args.model, num_classes, args.img_size)
    print(f"Model: {args.model} | img_size: {img_size}")
    model = model.to(device)

    # 가중치 저장 디렉토리 (원래 best.pth 저장 위치와 동일: models/weight/)
    weight_dir = Path(__file__).parent / "weight"
    weight_dir.mkdir(parents=True, exist_ok=True)

    # 이미 저장된 에폭 중 가장 큰 번호를 시작 오프셋으로 (없으면 0)
    start_offset = find_start_epoch(weight_dir, args.model)

    # 학습 (연속 저장 인자 전달) — 기본 학습 흐름은 그대로
    best_model, best_acc = train(
        model, train_loader, val_loader, device,
        epochs=args.epochs, lr=args.lr,
        weight_dir=weight_dir, model_name=args.model, start_epoch_offset=start_offset
    )

    # best 저장 (원본 동작 유지)
    save_path = weight_dir / f"{args.model}_best.pth"
    torch.save({
        "model": best_model.state_dict(),
        "classes": idx_to_class,
        "img_size": img_size
    }, save_path)
    print("Saved weight ->", save_path)

if __name__ == "__main__":
    main()
