# models/classifier/cascade/export_to_onnx.py
import torch, torch.nn as nn
from torchvision import models
from pathlib import Path

# 기존 학습 가중치
ckpt = torch.load("weight/mobilenet_v3_large_best.pth", map_location="cpu")
classes = ckpt.get("classes")
num_classes = len(classes) if classes else 13

# mobilenet_v3_large 모델 생성
m = models.mobilenet_v3_large(weights=None)
in_feat = m.classifier[-1].in_features
m.classifier[-1] = nn.Linear(in_feat, num_classes)
m.load_state_dict(ckpt["model"], strict=True)
m.eval()

# export to ONNX
onnx_path = Path("mobilenet_v3_large_best.onnx")
dummy = torch.randn(1, 3, 224, 224)
torch.onnx.export(m, dummy, onnx_path.as_posix(),
    input_names=["input"], output_names=["logits"], opset_version=12)

print("✓ ONNX saved:", onnx_path)
