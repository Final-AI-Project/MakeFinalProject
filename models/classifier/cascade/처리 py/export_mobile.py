import torch
from torch.utils.mobile_optimizer import optimize_for_mobile
from infer_classifier import build_model, load_labels
from pathlib import Path

ROOT = Path(__file__).parent
ckpt = torch.load(ROOT/"weight/mobilenet_v3_large_best.pth", map_location="cpu")
idx_to_class = ckpt.get("classes") or load_labels(ROOT/"labels.txt")
model, _ = build_model("mobilenet_v3_large", num_classes=len(idx_to_class))
model.load_state_dict(ckpt["model"]); model.eval()
ts = torch.jit.trace(model, torch.randn(1,3,224,224))
opt = optimize_for_mobile(ts)
opt._save_for_lite_interpreter(str(ROOT/"weight/mobilenet_v3_large_best.ptl"))
print("Saved:", ROOT/"weight/mobilenet_v3_large_best.ptl")