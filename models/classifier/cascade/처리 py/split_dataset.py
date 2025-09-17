# models/classifier/split_dataset.py
import os
import shutil
import random
import argparse
from pathlib import Path

def split_dataset(root_dir="plants-dataset", sample_dir="sample", train_ratio=0.8, seed=42, move=False):
    random.seed(seed)

    root = Path(root_dir)
    sample_path = root / sample_dir
    train_path  = root / "train"
    val_path    = root / "val"

    print(f"[DEBUG] root_dir={root.resolve()}")
    print(f"[DEBUG] sample_path={sample_path.resolve()}")

    if not sample_path.exists():
        msg = [
            f"[ERROR] sample 폴더를 찾지 못했습니다: {sample_path}",
            "",
            "해결 방법:",
            f"  1) 폴더를 이 위치로 옮기기: {sample_path}",
            f"  2) 또는 명령에 --root_dir 로 실제 위치 지정하기",
            "",
            "예시:",
            "  python models/classifier/split_dataset.py --root_dir models/plants-dataset",
        ]
        raise FileNotFoundError("\n".join(msg))

    # train/val 초기화
    for p in [train_path, val_path]:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)

    op = shutil.move if move else shutil.copy2

    # 클래스별 분할
    for class_dir in sample_path.iterdir():
        if not class_dir.is_dir():
            continue
        cls = class_dir.name
        images = [p for p in class_dir.iterdir() if p.suffix.lower() in [".jpg",".jpeg",".png",".bmp",".webp"]]
        random.shuffle(images)

        n_train = int(len(images) * train_ratio)
        train_imgs = images[:n_train]
        val_imgs   = images[n_train:]

        (train_path/cls).mkdir(parents=True, exist_ok=True)
        (val_path/cls).mkdir(parents=True, exist_ok=True)

        for src in train_imgs:
            op(str(src), str(train_path/cls/src.name))
        for src in val_imgs:
            op(str(src), str(val_path/cls/src.name))

        print(f"{cls}: train {len(train_imgs)} | val {len(val_imgs)}")

    print("\n✅ Split 완료!")
    print(f"Train dir: {train_path.resolve()}")
    print(f"Val dir:   {val_path.resolve()}")
    if move:
        print("⚠️ 원본 sample 파일들은 이동되었습니다. (복사가 아님)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root_dir",  type=str, default="plants-dataset", help="데이터 루트(여기에 sample/train/val 존재)")
    ap.add_argument("--sample_dir",type=str, default="sample", help="샘플 폴더명")
    ap.add_argument("--train_ratio", type=float, default=0.8, help="train 비율 (기본 0.8)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--move", action="store_true", help="복사 대신 이동")
    args = ap.parse_args()

    split_dataset(
        root_dir=args.root_dir,
        sample_dir=args.sample_dir,
        train_ratio=args.train_ratio,
        seed=args.seed,
        move=args.move
    )

if __name__ == "__main__":
    main()

# python models/classifier/cascade.py --data_root models/plants-dataset --model efficientnet_b0 --epochs 10 --weighted_sampler
# python models/classifier/cascade.py --data_root models/plants-dataset --model mobilenet_v3_large --epochs 10 --weighted_sampler
