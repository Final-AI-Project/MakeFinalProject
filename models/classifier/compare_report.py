# models/classifier/compare_report.py
import os, time, csv
from pathlib import Path
import argparse
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torchvision.models import MobileNet_V3_Large_Weights, EfficientNet_B0_Weights
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def build_model(name, num_classes, img_size_hint=224):
    n = name.lower()
    if n in ["mobilenet","mobilenet_v3_large"]:
        m = models.mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    elif n in ["efficientnet_b0","effnet_b0","efficientnet"]:
        m = models.efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        in_feat = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_feat, num_classes)
        rec = 224
    else:
        raise ValueError("지원 모델: mobilenet_v3_large | efficientnet_b0")
    if img_size_hint != rec:
        print(f"[INFO] {name} 권장 입력 {rec}, 현재 {img_size_hint} (진행 가능).")
    return m, rec

def load_ckpt(p):
    ck = torch.load(p, map_location="cpu")
    return ck["model"], ck.get("classes"), int(ck.get("img_size", 224))

def count_params(model): return sum(p.numel() for p in model.parameters())
def bytes_mb(path): return os.path.getsize(path)/1024/1024

def build_val_loader(val_dir, img_size, batch=32, workers=0):
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

@torch.no_grad()
def eval_full(model, loader, device):
    model.eval().to(device)
    all_pred, all_prob, all_true, all_paths = [], [], [], []
    softmax = torch.nn.Softmax(dim=1)
    for (x, y), paths in zip(loader, getattr(loader.dataset, 'imgs', [])):
        x, y = x.to(device), y.to(device)
        out = model(x)
        prob = softmax(out).cpu().numpy()
        pred = out.argmax(1).cpu().numpy()
        all_pred.append(pred)
        all_prob.append(prob)
        all_true.append(y.cpu().numpy())
    # dataset.imgs는 (path, label) 리스트
    all_paths = [p for p,_ in loader.dataset.imgs]
    return (np.concatenate(all_pred),
            np.concatenate(all_prob),
            np.concatenate(all_true),
            all_paths)

def topk_acc(probs, true, k=1):
    topk = np.argsort(-probs, axis=1)[:, :k]
    return float(np.mean([t in topk[i] for i,t in enumerate(true)]))

def save_confusion_png(cm, classes, out_png):
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(cm, interpolation='nearest')
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=np.arange(len(classes)), yticks=np.arange(len(classes)),
           xticklabels=classes, yticklabels=classes, ylabel='True', xlabel='Pred')
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    # 값 표기(작은 셋용)
    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'), ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black", fontsize=8)
    plt.tight_layout()
    fig.savefig(out_png, dpi=160)
    plt.close(fig)

@torch.no_grad()
def benchmark_latency(model, img_size, device, iters=50, warmup=10):
    model.eval().to(device)
    x = torch.randn(1,3,img_size,img_size, device=device)
    for _ in range(warmup): _ = model(x)
    if device.type == "cuda": torch.cuda.synchronize()
    t0 = time.time()
    for _ in range(iters): _ = model(x)
    if device.type == "cuda": torch.cuda.synchronize()
    return (time.time()-t0)/iters*1000.0

def dump_misclassified(paths, true, pred, classes, out_dir, limit=20):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    wrong_idx = np.where(true != pred)[0][:limit]
    for i in wrong_idx:
        src = Path(paths[i])
        tgt = out / f"pred_{classes[pred[i]]}__true_{classes[true[i]]}__{src.name}"
        try:
            Image.open(src).save(tgt)
        except Exception:
            pass
    return len(wrong_idx)

def run_one(name, weight_path, data_root, device, batch=32, workers=0):
    state, cls_map, img_size = load_ckpt(weight_path)
    if cls_map is None:
        raise ValueError(f"{weight_path} 에 classes 매핑이 없음")
    classes = [cls_map[i] for i in range(len(cls_map))]
    num_classes = len(classes)

    model, rec = build_model(name, num_classes, img_size)
    model.load_state_dict(state)

    # metrics: size/params
    f_mb = bytes_mb(weight_path)
    params_m = count_params(model)/1e6

    # latency
    latency_ms = benchmark_latency(model, img_size or rec, device)

    # val
    val_dir = Path(data_root)/"val"
    val_acc = top1 = top3 = None
    per_class = {}
    conf_png = None
    if val_dir.exists() and any(val_dir.iterdir()):
        ds, ld = build_val_loader(val_dir, img_size or rec, batch, workers)
        y_pred, y_prob, y_true, paths = eval_full(model, ld, device)
        cm = confusion_matrix(y_true, y_pred, labels=list(range(num_classes)))
        conf_png = Path(weight_path).with_suffix(f".{name}.cm.png")
        save_confusion_png(cm, classes, conf_png)

        rep = classification_report(y_true, y_pred, target_names=classes, output_dict=True, zero_division=0)
        per_class = {k: {"precision":v["precision"], "recall":v["recall"], "f1":v["f1-score"]} for k,v in rep.items() if k in classes}

        top1 = topk_acc(y_prob, y_true, k=1)
        top3 = topk_acc(y_prob, y_true, k=3 if num_classes>=3 else num_classes)

        # misclassified dump
        dump_dir = Path(weight_path).with_suffix(f".{name}.miscls")
        dumped = dump_misclassified(paths, y_true, y_pred, classes, dump_dir, limit=30)

    return {
        "model": name,
        "weight": str(weight_path),
        "img_size": img_size,
        "params_M": params_m,
        "weight_MB": f_mb,
        "latency_ms_per_img": latency_ms,
        "top1": top1,
        "top3": top3,
        "per_class": per_class,
        "confusion_png": str(conf_png) if conf_png else None,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mobilenet_weights", required=True)
    ap.add_argument("--efficientnet_weights", required=True)
    ap.add_argument("--mobilenet_name", default="mobilenet_v3_large")
    ap.add_argument("--efficientnet_name", default="efficientnet_b0")
    ap.add_argument("--data_root", default="models/plants-dataset")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    device = torch.device(args.device)
    results = []
    for name, w in [(args.mobilenet_name, args.mobilenet_weights),
                    (args.efficientnet_name, args.efficientnet_weights)]:
        print(f"\n[RUN] {name} from {w}")
        results.append(run_one(name, Path(w), args.data_root, device, args.batch, args.workers))

    # print table
    print("\n=== Summary ===")
    print("{:<20} {:>8} {:>9} {:>11} {:>15} {:>8} {:>8}".format(
        "model","img","paramsM","weightMB","latency(ms)","top1","top3"))
    for r in results:
        print("{:<20} {:>8} {:>9.2f} {:>11.2f} {:>15.2f} {:>8} {:>8}".format(
            r["model"], r["img_size"], r["params_M"], r["weight_MB"], r["latency_ms_per_img"],
            f"{r['top1']:.4f}" if r["top1"] is not None else "N/A",
            f"{r['top3']:.4f}" if r["top3"] is not None else "N/A"
        ))

    # save CSV + per-class metrics
    out_csv = Path("models/classifier/compare_report.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model","img_size","params_M","weight_MB","latency_ms_per_img","top1","top3","confusion_png"])
        for r in results:
            w.writerow([r["model"], r["img_size"], f"{r['params_M']:.4f}", f"{r['weight_MB']:.2f}",
                        f"{r['latency_ms_per_img']:.2f}",
                        f"{r['top1']:.4f}" if r["top1"] is not None else "N/A",
                        f"{r['top3']:.4f}" if r["top3"] is not None else "N/A",
                        r["confusion_png"] or ""])
    # per-class separate CSVs
    for r in results:
        if r["per_class"]:
            pcsv = Path(f"models/classifier/per_class_{r['model']}.csv")
            with open(pcsv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["class","precision","recall","f1"])
                for cls, m in r["per_class"].items():
                    w.writerow([cls, f"{m['precision']:.4f}", f"{m['recall']:.4f}", f"{m['f1']:.4f}"])
    print(f"\nSaved: {out_csv}")
    for r in results:
        if r["confusion_png"]:
            print(f"Saved confusion: {r['confusion_png']}")

if __name__ == "__main__":
    main()
