# 파일 분류 전용 스크립트
import os
import shutil
import random
from pathlib import Path

def split_dataset(root_dir="plants-dataset", sample_dir="sample", train_ratio=0.8, seed=2025):
    random.seed(seed)
    
    root = Path(root_dir)
    sample_path = root / sample_dir
    train_path  = root / "train"
    val_path    = root / "val"

    # train/val 디렉토리 새로 생성
    for p in [train_path, val_path]:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)

    # 클래스 단위로 분할
    for class_dir in sample_path.iterdir():
        if not class_dir.is_dir():
            continue
        cls_name = class_dir.name
        images = list(class_dir.glob("*.*"))
        random.shuffle(images)

        n_train = int(len(images) * train_ratio)
        train_imgs = images[:n_train]
        val_imgs   = images[n_train:]

        # 클래스별 폴더 생성
        (train_path/cls_name).mkdir(parents=True, exist_ok=True)
        (val_path/cls_name).mkdir(parents=True, exist_ok=True)

        # 복사 (원하면 move로 변경 가능)
        for img in train_imgs:
            shutil.copy(img, train_path/cls_name/img.name)
        for img in val_imgs:
            shutil.copy(img, val_path/cls_name/img.name)

        print(f"{cls_name}: train {len(train_imgs)} | val {len(val_imgs)}")

    print("\n✅ Split 완료!")
    print(f"Train dir: {train_path}")
    print(f"Val dir:   {val_path}")

if __name__ == "__main__":
    split_dataset()
