# export_to_onnx.py
# 사용 예:
#   (cascade 폴더에서)
#   python export_to_onnx.py --weights weight\mobilenet_v3_large_best.pth --labels labels.txt --out mobilenet_v3_large_best.onnx --verify
#
# 옵션:
#   --model mobilenet_v3_large        # 커스텀 빌더가 model_name을 요구할 때 지정 가능(기본 mobilenet_v3_large)
#   --input-size 224 224              # 입력 크기 (기본 224 224)
#   --opset 12                        # ONNX opset (기본 12)
#   --dynamic                         # 배치 축 동적 (없으면 고정 1x3xHxW)
#   --verify                          # 내보낸 onnx를 onnxruntime로 1번 추론 검증

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import argparse
import importlib.util
import sys

import torch
import torch.nn as nn


HERE = Path(__file__).resolve().parent
DEFAULT_MODEL_NAME = "mobilenet_v3_large"

def ensure_module(x):
    if isinstance(x, nn.Module):
        return x
    if isinstance(x, (list, tuple)):
        for item in x:
            if isinstance(item, nn.Module):
                return item
    raise TypeError(f"Custom builder returned non-module: {type(x)}")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export PyTorch classifier to ONNX")
    p.add_argument("--weights", type=str, required=True, help="Path to .pth weights")
    p.add_argument("--labels",  type=str, required=True, help="Path to labels.txt")
    p.add_argument("--out",     type=str, required=True, help="Output ONNX path")

    p.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help=f"model_name for custom builder (default: {DEFAULT_MODEL_NAME})")
    p.add_argument("--input-size", type=int, nargs=2, default=[224, 224], metavar=("W", "H"), help="input width height (default: 224 224)")
    p.add_argument("--opset", type=int, default=12, help="ONNX opset version (default: 12)")
    p.add_argument("--dynamic", action="store_true", help="export with dynamic batch axis N")
    p.add_argument("--verify", action="store_true", help="run onnx.checker & ort inference")

    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────────────────────

def load_labels(labels_path: Path) -> list[str]:
    lines = labels_path.read_text(encoding="utf-8").splitlines()
    labels = [ln.strip() for ln in lines if ln.strip()]
    if len(labels) < 2:
        raise RuntimeError(f"labels.txt 라인 수가 이상함: {len(labels)}")
    return labels


def import_custom_module(py_path: Path):
    spec = importlib.util.spec_from_file_location(py_path.stem, str(py_path))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_model(num_classes: int, model_name: str, custom_mod=None) -> nn.Module:
    """
    1) infer_classifier.py 가 있으면 그 안의 빌더들 시그니처를 폭넓게 시도
    2) 실패하면 torchvision mobilenet_v3_large 로 백업
    """
    # 1) 커스텀 모듈 시도
    if custom_mod is not None:
        for cand in ["build_model", "build_classifier", "create_model"]:
            fn = getattr(custom_mod, cand, None)
            if not callable(fn):
                continue

            # 다양한 시그니처 시도
            # (a) 키워드 인자
            try:
                print(f"[INFO] 커스텀 빌더 사용: {cand}({model_name!r}, num_classes={num_classes}) [kw]")
                m = fn(model_name=model_name, num_classes=num_classes)
                return m
            except TypeError:
                pass

            # (b) 위치 인자
            try:
                print(f"[INFO] 커스텀 빌더 사용: {cand}({model_name!r}, {num_classes}) [pos]")
                m = fn(model_name, num_classes)
                return m
            except TypeError:
                pass

            # (c) num_classes만 받는 형태
            try:
                print(f"[INFO] 커스텀 빌더 사용: {cand}(num_classes={num_classes}) [minimal]")
                m = fn(num_classes=num_classes)
                return m
            except TypeError:
                # 다음 후보로
                continue

        print("[WARN] infer_classifier.py 내 사용 가능한 빌더 함수 시그니처가 없음 → torchvision 백업 사용")

    # 2) torchvision mobilenet_v3_large 백업
    from torchvision.models import mobilenet_v3_large
    m = mobilenet_v3_large(weights=None)
    # classifier 끝의 Linear 교체
    if isinstance(m.classifier, nn.Sequential) and isinstance(m.classifier[-1], nn.Linear):
        in_f = m.classifier[-1].in_features
        m.classifier[-1] = nn.Linear(in_f, num_classes)
    else:
        # 방어: 끝 Linear를 뒤에서부터 탐색
        last_lin = None
        for mod in reversed(list(m.classifier.modules())):
            if isinstance(mod, nn.Linear):
                last_lin = mod
                break
        if last_lin is None:
            raise RuntimeError("cannot locate final Linear in classifier")
        in_f = last_lin.in_features
        m.classifier = nn.Sequential(nn.Linear(in_f, num_classes))
    print("[INFO] torchvision mobilenet_v3_large built (fallback)")
    return m


def load_weights(model: nn.Module, ckpt_path: Path):
    """
    다양한 체크포인트 포맷 대응 + DataParallel 'module.' prefix 제거
    """
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    if isinstance(ckpt, dict):
        if "state_dict" in ckpt:
            sd = ckpt["state_dict"]
        elif "model" in ckpt:
            sd = ckpt["model"]
        else:
            sd = ckpt
    else:
        try:
            model.load_state_dict(ckpt.state_dict())
            print("[INFO] loaded from full model object")
            return
        except Exception as e:
            raise RuntimeError(f"unknown checkpoint format: {type(ckpt)} {e}")

    # strip 'module.' prefix
    sd = { (k[7:] if k.startswith("module.") else k): v for k, v in sd.items() }
    try:
        model.load_state_dict(sd, strict=True)
        print("[INFO] state_dict strict=True loaded")
    except Exception as e:
        print(f"[WARN] strict=True failed: {e}")
        model.load_state_dict(sd, strict=False)
        print("[INFO] state_dict strict=False loaded")


def export_onnx(
    model: nn.Module,
    out_path: Path,
    input_size: Tuple[int, int],
    opset: int,
    dynamic: bool
):
    model.eval()
    w, h = input_size
    dummy = torch.zeros(1, 3, h, w, dtype=torch.float32)

    dynamic_axes = None
    if dynamic:
        dynamic_axes = {"input": {0: "N"}, "logits": {0: "N"}}

    torch.onnx.export(
        model,
        dummy,
        str(out_path),
        export_params=True,
        opset_version=opset,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes=dynamic_axes,
    )
    print(f"[INFO] ONNX export done → {out_path}")


def verify_onnx(out_path: Path, input_size: Tuple[int, int]):
    import onnx
    import onnxruntime as ort
    w, h = input_size

    onnx_model = onnx.load(str(out_path))
    onnx.checker.check_model(onnx_model)
    print("[INFO] onnx.checker OK")

    sess = ort.InferenceSession(str(out_path), providers=["CPUExecutionProvider"])
    outs = sess.run(None, {"input": torch.zeros(1, 3, h, w, dtype=torch.float32).numpy()})
    shapes = [list(getattr(o, "shape", [])) for o in outs]
    print("[INFO] ort.run OK; logits shape:", shapes)


def main():
    args = parse_args()

    weights_path = Path(args.weights).resolve()
    labels_path  = Path(args.labels).resolve()
    out_path     = Path(args.out).resolve()
    model_name   = args.model or DEFAULT_MODEL_NAME
    w, h         = tuple(args["input_size"] if isinstance(args, dict) else args.input_size)
    opset        = args.opset
    dynamic      = args.dynamic

    labels = load_labels(labels_path)
    num_classes = len(labels)

    print(f"[INFO] num_classes={num_classes}, input={w}x{h}, opset={opset}")
    print(f"[INFO] weights={weights_path}")
    print(f"[INFO] labels={labels_path}")
    print(f"[INFO] out={out_path}")

    # 커스텀 빌더 로드 시도
    custom_py = HERE / "infer_classifier.py"
    custom_mod = None
    if custom_py.exists():
        try:
            custom_mod = import_custom_module(custom_py)
            if custom_mod is not None:
                print(f"[INFO] infer_classifier.py 로드 성공: {custom_py.name}")
        except Exception as e:
            print(f"[WARN] infer_classifier.py 로드 실패: {e}")

    # 모델 구성 & 가중치 로드
    model = build_model(num_classes=num_classes, model_name=model_name, custom_mod=custom_mod)
    model = ensure_module(model)

    # ONNX 내보내기
    export_onnx(model, out_path, (w, h), opset, dynamic)

    # 검증
    if args.verify:
        verify_onnx(out_path, (w, h))


if __name__ == "__main__":
    torch.set_num_threads(1)
    main()
