# models/classifier/compare_models.py
import argparse, os, time
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    EfficientNet_B0_Weights,
    EfficientNet_B2_Weights,
    EfficientNet_B3_Weights,
)

# -------- Model factory --------
def build_model(model_name: str, num_classes: int, img_size_hint: int = 224):
    name = model_name.lower()
    if name in ["mobilenet", "mobilenet_v3_large"]:
        m = models.mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b0", "effnet_b0"]:
        m = models.efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif name in ["efficientnet_b2", "effnet_b2"]:
        m = models.efficientnet_b2(weights=EfficientNet_B2_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 260
    elif name in ["efficientnet_b3", "effnet_b3"]:
        m = models.efficientnet_b3(weights=EfficientNet_B3_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 300
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    # warn only
    if img_size_hint and img_size_hint != rec:
        print(f"[INFO] {model_name} recommended input {rec}, current hint {img_size_hint}. (OK)")
    return m, rec

# -------- Metrics --------
@torch.no_grad()
def evaluate_top1(model, loader, device):
    model.eval().to(device)
    correct, total = 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        pred = out.argmax(1)
        correct += (pred == y).sum().item()
        total += y.size(0)
    return correct / max(total, 1)

@torch.no_grad()
def benchmark_latency(model, img_size, device, n_warmup=10, n_iters=50):
    model.eval().to(device)
    dummy = torch.randn(1, 3, img_size, img_size, device=device)
    # warmup
    for _ in range(n_warmup):
        _ = model(dummy)
    if device.type == "cuda":
        torch.cuda.synchronize()
    # measure
    t0 = time.time()
    for _ in range(n_iters):
        _ = model(dummy)
    if device.type == "cuda":
        torch.cuda.synchronize()
    t1 = time.time()
    ms = (t1 - t0) / n_iters * 1000.0
    return ms

def load_ckpt(ckpt_path: Path):
    ckpt = torch.load(ckpt_path, map_location="cpu")
    cls_map = ckpt.get("classes", None)
    img_size = int(ckpt.get("img_size", 224))
    state = ckpt["model"]
    return state, cls_map, img_size

def count_params(model):
    return sum(p.numel() for p in model.parameters())

def bytes_to_mb(b): return b / 1024 / 1024

# -------- Val loader (optional) --------
def build_val_loader(val_dir: Path, img_size: int, batch: int, workers: int):
    mean=(0.485,0.456,0.406); std=(0.229,0.224,0.225)
    tfm = transforms.Compose([
        transforms.Resize(int(img_size*1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    ds = datasets.ImageFolder(str(val_dir), transform=tfm)
    ld = torch.utils.data.DataLoader(ds, batch_size=batch, shuffle=False,
                                     num_workers=workers, pin_memory=torch.cuda.is_available())
    return ds, ld

# -------- Main --------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mobilenet_weights", type=str, required=True, help="path to mobilenet_v3_large_best.pth")
    ap.add_argument("--efficientnet_weights", type=str, required=True, help="path to efficientnet_b0_best.pth")
    ap.add_argument("--mobilenet_name", type=str, default="mobilenet_v3_large")
    ap.add_argument("--efficientnet_name", type=str, default="efficientnet_b0")
    ap.add_argument("--data_root", type=str, default="models/plants-dataset", help="dataset root that contains val/")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    device = torch.device(args.device)
    data_root = Path(args.data_root)
    val_dir = data_root / "val"

    rows = []

    for model_name, weight_path in [
        (args.mobilenet_name, Path(args.mobilenet_weights)),
        (args.efficientnet_name, Path(args.efficientnet_weights)),
    ]:
        if not weight_path.exists():
            raise FileNotFoundError(f"Weight not found: {weight_path}")

        # load checkpoint
        state, cls_map, img_size = load_ckpt(weight_path)
        if cls_map is None:
            raise ValueError(f"'classes' mapping not found in checkpoint: {weight_path}")
        num_classes = len(cls_map)

        # build & load model
        model, rec = build_model(model_name, num_classes, img_size)
        model.load_state_dict(state)

        # metrics
        fsize_mb = bytes_to_mb(os.path.getsize(weight_path))
        params_m = count_params(model) / 1e6
        latency_ms = benchmark_latency(model, img_size or rec, device)

        # val acc (optional)
        val_acc = None
        if val_dir.exists() and any(val_dir.iterdir()):
            ds, val_loader = build_val_loader(val_dir, img_size or rec, args.batch, args.workers)
            # safeguard: class count must match
            if len(ds.classes) != num_classes:
                print(f"[WARN] val classes ({len(ds.classes)}) != ckpt classes ({num_classes}). Accuracy may be invalid.")
            val_acc = evaluate_top1(model, val_loader, device)

        rows.append({
            "model": model_name,
            "file": str(weight_path),
            "img_size": img_size,
            "params_M": params_m,
            "weight_MB": fsize_mb,
            "latency_ms/img": latency_ms,
            "val_acc": val_acc,
        })

    # pretty print
    print("\n=== Comparison ===")
    hdr = ["model", "img_size", "params_M", "weight_MB", "latency_ms/img", "val_acc"]
    print("{:<20} {:>8} {:>10} {:>11} {:>15} {:>9}".format(*hdr))
    for r in rows:
        print("{:<20} {:>8} {:>10.2f} {:>11.2f} {:>15.2f} {:>9}".format(
            r["model"], r["img_size"], r["params_M"], r["weight_MB"], r["latency_ms/img"],
            f"{r['val_acc']:.4f}" if r["val_acc"] is not None else "N/A"
        ))

if __name__ == "__main__":
    main()
