"""
Model Training Classifier
식물 분류 모델 학습
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import transforms, datasets
import timm
import numpy as np
from typing import Dict, Any, Optional, Callable
import logging
from tqdm import tqdm
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelTrainer:
    """모델 학습기"""
    
    def __init__(
        self,
        dataset_source: str = "samples",
        epochs: int = 10,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        freeze_backbone: bool = False,
        output_name: str = "plant_whisperer_model",
        validation_split: float = 0.2,
        random_seed: int = 42
    ):
        """
        초기화
        
        Args:
            dataset_source: 데이터셋 소스 (samples, local, plantvillage)
            epochs: 학습 에포크 수
            batch_size: 배치 크기
            learning_rate: 학습률
            freeze_backbone: 백본 고정 여부
            output_name: 출력 모델명
            validation_split: 검증 데이터 비율
            random_seed: 랜덤 시드
        """
        self.dataset_source = dataset_source
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.freeze_backbone = freeze_backbone
        self.output_name = output_name
        self.validation_split = validation_split
        self.random_seed = random_seed
        
        # 디바이스 설정
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"사용 디바이스: {self.device}")
        
        # 랜덤 시드 설정
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)
        
        # 모델 및 데이터로더 초기화
        self.model = None
        self.train_loader = None
        self.val_loader = None
        self.criterion = None
        self.optimizer = None
        self.scheduler = None
        
        # 클래스 정보
        self.class_names = self._get_class_names()
        self.num_classes = len(self.class_names["species"]) + len(self.class_names["disease"])
        
        # 학습 결과 저장
        self.train_history = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "best_val_acc": 0.0,
            "best_epoch": 0
        }
    
    def _get_class_names(self) -> Dict[str, list]:
        """클래스명 반환"""
        return {
            "species": [
                "토마토", "고추", "상추", "양파", "마늘", "당근", "감자", "고구마",
                "배추", "무", "오이", "호박", "가지", "피망", "브로콜리", "양배추",
                "시금치", "부추", "파", "생강", "우엉", "연근", "미나리", "깻잎",
                "바질", "로즈마리", "라벤더", "민트", "레몬그라스", "타임"
            ],
            "disease": [
                "건강", "세균성점무늬병", "세균성시들음병", "세균성썩음병",
                "검은점무늬병", "노균병", "흰가루병", "잎마름병", "바이러스병",
                "선충병", "곰팡이병", "탄저병", "역병", "겹무늬병", "점무늬병"
            ]
        }
    
    def _create_model(self) -> nn.Module:
        """모델 생성"""
        # EfficientNet-B0 기반 모델
        model = timm.create_model(
            "efficientnet_b0",
            pretrained=True,
            num_classes=self.num_classes
        )
        
        # 백본 고정 (선택적)
        if self.freeze_backbone:
            for param in model.parameters():
                param.requires_grad = False
            # 분류기만 학습 가능하도록 설정
            for param in model.classifier.parameters():
                param.requires_grad = True
        
        return model
    
    def _get_transforms(self) -> Dict[str, transforms.Compose]:
        """데이터 변환 파이프라인"""
        # 학습용 변환 (증강 포함)
        train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 검증용 변환 (증강 없음)
        val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        return {
            "train": train_transform,
            "val": val_transform
        }
    
    def _load_dataset(self) -> datasets.DatasetFolder:
        """데이터셋 로드"""
        if self.dataset_source == "samples":
            # 샘플 데이터셋 로드
            dataset_path = "storage/samples"
            if not os.path.exists(dataset_path):
                # 샘플 데이터 생성
                self._create_sample_dataset()
        elif self.dataset_source == "local":
            dataset_path = "storage/samples"
        else:
            raise ValueError(f"지원하지 않는 데이터셋 소스: {self.dataset_source}")
        
        # 데이터셋 로드
        dataset = datasets.DatasetFolder(
            root=dataset_path,
            loader=self._image_loader,
            extensions=('.jpg', '.jpeg', '.png', '.webp'),
            transform=self._get_transforms()["train"]  # 기본값
        )
        
        logger.info(f"데이터셋 로드 완료: {len(dataset)}개 샘플, {len(dataset.classes)}개 클래스")
        return dataset
    
    def _image_loader(self, path: str):
        """이미지 로더"""
        from PIL import Image
        return Image.open(path).convert('RGB')
    
    def _create_sample_dataset(self):
        """샘플 데이터셋 생성"""
        import shutil
        from PIL import Image, ImageDraw, ImageFont
        import random
        
        sample_dir = "storage/samples"
        os.makedirs(sample_dir, exist_ok=True)
        
        # 샘플 클래스 생성
        sample_classes = ["토마토", "고추", "상추", "양파", "마늘"]
        
        for class_name in sample_classes:
            class_dir = os.path.join(sample_dir, class_name)
            os.makedirs(class_dir, exist_ok=True)
            
            # 각 클래스당 10개 샘플 생성
            for i in range(10):
                # 간단한 샘플 이미지 생성
                img = Image.new('RGB', (224, 224), color=(
                    random.randint(50, 200),
                    random.randint(100, 255),
                    random.randint(50, 150)
                ))
                
                # 텍스트 추가
                draw = ImageDraw.Draw(img)
                try:
                    # 폰트 설정 (시스템 폰트 사용)
                    font = ImageFont.load_default()
                except:
                    font = None
                
                draw.text((10, 10), f"{class_name} {i+1}", fill=(255, 255, 255), font=font)
                
                # 파일 저장
                img_path = os.path.join(class_dir, f"{class_name}_{i+1}.jpg")
                img.save(img_path)
        
        logger.info(f"샘플 데이터셋 생성 완료: {sample_dir}")
    
    def _create_data_loaders(self, dataset: datasets.DatasetFolder):
        """데이터 로더 생성"""
        # 데이터셋 분할
        val_size = int(len(dataset) * self.validation_split)
        train_size = len(dataset) - val_size
        
        train_dataset, val_dataset = random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(self.random_seed)
        )
        
        # 검증 데이터셋에 변환 적용
        val_dataset.dataset.transform = self._get_transforms()["val"]
        
        # 데이터 로더 생성
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True
        )
        
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True
        )
        
        logger.info(f"데이터 로더 생성 완료: 학습 {len(train_dataset)}개, 검증 {len(val_dataset)}개")
    
    def _setup_training(self):
        """학습 설정"""
        # 모델 생성
        self.model = self._create_model().to(self.device)
        
        # 손실 함수
        self.criterion = nn.CrossEntropyLoss()
        
        # 옵티마이저
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=0.01
        )
        
        # 스케줄러
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=self.epochs
        )
        
        logger.info("학습 설정 완료")
    
    async def train(self, progress_callback: Optional[Callable] = None):
        """모델 학습"""
        try:
            # 데이터셋 및 로더 준비
            dataset = self._load_dataset()
            self._create_data_loaders(dataset)
            
            # 학습 설정
            self._setup_training()
            
            # 학습 루프
            for epoch in range(self.epochs):
                # 학습
                train_loss, train_acc = self._train_epoch()
                
                # 검증
                val_loss, val_acc = self._validate_epoch()
                
                # 학습률 조정
                self.scheduler.step()
                
                # 결과 저장
                self.train_history["train_loss"].append(train_loss)
                self.train_history["train_acc"].append(train_acc)
                self.train_history["val_loss"].append(val_loss)
                self.train_history["val_acc"].append(val_acc)
                
                # 최고 성능 모델 저장
                if val_acc > self.train_history["best_val_acc"]:
                    self.train_history["best_val_acc"] = val_acc
                    self.train_history["best_epoch"] = epoch
                    await self._save_model("best")
                
                # 진행상황 콜백
                if progress_callback:
                    progress_callback(epoch + 1, train_loss, train_acc)
                
                logger.info(
                    f"Epoch {epoch+1}/{self.epochs} - "
                    f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, "
                    f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
                )
            
            # 최종 모델 저장
            await self._save_model("final")
            
            # 학습 결과 저장
            await self._save_training_history()
            
            logger.info("학습 완료!")
            
        except Exception as e:
            logger.error(f"학습 중 오류 발생: {str(e)}")
            raise
    
    def _train_epoch(self) -> tuple:
        """한 에포크 학습"""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(self.train_loader):
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            total += target.size(0)
        
        avg_loss = total_loss / len(self.train_loader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    def _validate_epoch(self) -> tuple:
        """한 에포크 검증"""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in self.val_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                loss = self.criterion(output, target)
                
                total_loss += loss.item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)
        
        avg_loss = total_loss / len(self.val_loader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    async def _save_model(self, suffix: str):
        """모델 저장"""
        try:
            models_dir = "storage/models"
            os.makedirs(models_dir, exist_ok=True)
            
            # PyTorch 모델 저장
            model_path = os.path.join(models_dir, f"{self.output_name}_{suffix}.pt")
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epoch': self.epochs,
                'train_history': self.train_history,
                'class_names': self.class_names,
                'model_config': {
                    'model_name': 'efficientnet_b0',
                    'num_classes': self.num_classes,
                    'freeze_backbone': self.freeze_backbone
                }
            }, model_path)
            
            logger.info(f"모델 저장 완료: {model_path}")
            
        except Exception as e:
            logger.error(f"모델 저장 실패: {str(e)}")
            raise
    
    async def _save_training_history(self):
        """학습 히스토리 저장"""
        try:
            history_path = f"storage/models/{self.output_name}_history.json"
            
            history_data = {
                "training_config": {
                    "dataset_source": self.dataset_source,
                    "epochs": self.epochs,
                    "batch_size": self.batch_size,
                    "learning_rate": self.learning_rate,
                    "freeze_backbone": self.freeze_backbone,
                    "validation_split": self.validation_split,
                    "random_seed": self.random_seed
                },
                "train_history": self.train_history,
                "class_names": self.class_names,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"학습 히스토리 저장 완료: {history_path}")
            
        except Exception as e:
            logger.error(f"학습 히스토리 저장 실패: {str(e)}")
            raise


if __name__ == "__main__":
    import asyncio
    
    # 학습 실행 예시
    async def main():
        trainer = ModelTrainer(
            dataset_source="samples",
            epochs=5,
            batch_size=16,
            learning_rate=0.001
        )
        
        await trainer.train()
    
    asyncio.run(main())
