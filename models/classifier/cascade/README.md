
# 실행 (가상환경에서):
(.venv) D:\hwan\AIFinalProject\models\classifier\cascade> pip install fastapi uvicorn pillow torch torchvision
(.venv) D:\hwan\AIFinalProject\models\classifier\cascade> uvicorn server:app --host 0.0.0.0 --port 4000


# plants-dataset/train, val 에 실제 식물 이미지 넣은 뒤
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model mobilenet_v3_large --epochs 10 --weighted_sampler



# Python 단일 명령어 추론
python infer_classifier.py --model mobilenet_v3_large --weights weight/mobilenet_v3_large_best.pth --image plants-dataset/val/mon/mon_102.jpg

# 프론트 연결용 추론 서버 실행
uvicorn server:app --host 0.0.0.0 --port 4000

# 모바일 온디바이스 실행 준비 (TorchScript)
python export_mobile.py











### 그 밖에 모델 테스트
# ShuffleNetV2
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model shufflenet_v2 --epochs 10 --weighted_sampler

# efficientnet_b0
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model efficientnet_b0 --epochs 20 --weighted_sampler

# GhostNet (timm 필요)
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model ghostnet --epochs 10 --weighted_sampler

# MobileViT(v2) (timm 필요)
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model mobilevitv2 --epochs 10 --weighted_sampler

# MobileNetV3-Large (기존)
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model mobilenet_v3_large --epochs 10 --weighted_sampler

# pth 로 비교
python models/classifier/cascade/compare_report.py --data_root models/plants-dataset --mobilenet_weights models/classifier/cascade/weight/mobilenet_v3_large_best.pth --ghostnet_weights models/classifier/cascade/weight/ghostnet_best.pth --mobilevitv2_weights models/classifier/cascade/weight/mobilevitv2_best.pth --shufflenet_v2_weights models/classifier/cascade/weight/shufflenet_v2_best.pth --efficientnet_b0_weights models/classifier/cascade/weight/efficientnet_b0_best.pth


# 📊 모델별 성능 비교 보고서 (compare_report.csv 기반)
1. 개요
이번 실험에서는 5개 모델을 비교했습니다.
* MobileNetV3-Large
* GhostNet
* MobileViT-V2
* ShuffleNet-V2
* EfficientNet-B0
비교 기준: 입력 크기, 파라미터 수, 모델 크기, 추론 속도, 정확도(Top-1/Top-3), 클래스별 Precision/Recall/F1.

2. 모델 크기 및 파라미터
| 모델              | 파라미터(M) | 모델 크기(MB) |
| --------------- | ------- | --------- |
| MobileNetV3-L   | 4.22    | 16.29     |
| GhostNet        | 3.92    | 15.21     |
| MobileViT-V2    | 4.40    | 16.93     |
| ShuffleNet-V2   | 1.27    | 5.00      |
| EfficientNet-B0 | 4.02    | 15.64     |
* MobileNetV3-L, GhostNet, EfficientNet-B0, MobileViT-V2는 모두 4M대 파라미터, 15~17MB 모델 크기.
* ShuffleNet-V2는 1.2M 파라미터, 5MB로 매우 가볍지만 성능이 떨어짐.
📈 그래프 (Params/Size)
* params_by_model.png
* size_by_model.png

3. 정확도 성능
| 모델              | Top-1     | Top-3 |
| --------------- | --------- | ----- |
| MobileNetV3-L   | 0.931     | 0.992 |
| GhostNet        | 0.931     | 0.977 |
| MobileViT-V2    | 0.923     | 0.989 |
| ShuffleNet-V2   | 0.521     | 0.820 |
| EfficientNet-B0 | **0.954** | 0.981 |
* EfficientNet-B0: Top-1 정확도 95.4%, 최고 성능.
* MobileNetV3-L & GhostNet: 93.1%, 안정적.
* MobileViT-V2: 92.3%, 약간 낮음.
* ShuffleNet-V2: 52.1%, 현저히 낮음.
📈 그래프 (Top-1 Accuracy)
* top1_by_model.png

4. 속도 (Latency)
| 모델              | Latency (ms/img) |
| --------------- | ---------------- |
| MobileNetV3-L   | **4.89**         |
| GhostNet        | 11.43            |
| MobileViT-V2    | 6.92             |
| ShuffleNet-V2   | 5.32             |
| EfficientNet-B0 | 6.21             |
* MobileNetV3-L: 가장 빠름 (4.89ms)
* EfficientNet-B0, MobileViT-V2: 6~7ms대
* ShuffleNet-V2: 5.3ms로 빠르지만 정확도 낮음
* GhostNet: 11ms, 상대적으로 느림
📈 그래프 (Latency)
* latency_by_model.png
* acc_vs_latency.png (정확도 vs 속도 트레이드오프)

5. 클래스별 성능 분석 (per_class CSV 기반)
* EfficientNet-B0: 전 클래스에서 안정적, Precision/Recall/F1 모두 고르게 높음.
* MobileNetV3-L: 전반적으로 강력하나 일부 클래스 Recall 낮음.
* GhostNet: 특정 클래스 Recall 손실 존재.
* MobileViT-V2: 안정적이지만 EfficientNet-B0보다 낮음.
* ShuffleNet-V2: 클래스별 편차 매우 큼, 일부 클래스 거의 실패.
📈 그래프
* Per-class F1 / Precision / Recall 비교 그래프 (앞서 제작)

6. 결론 및 권고
* 최고 성능 모델: EfficientNet-B0 (정확도 우선 환경)
* 균형형 모델: MobileNetV3-L (속도+정확도 균형, 모바일 앱 적합)
* 후보 제외: ShuffleNet-V2 (정확도 부족)
* 조건부 후보: GhostNet / MobileViT-V2 (보조 용도 가능)

✅ 내 선택
온디바이스(React Native/Expo) 실시간 추론: MobileNetV3-Large
이유: Top-1 93.1% vs 6~7ms급보다 더 빠른 4.89ms, 파라미터 4.22M로 가볍고 모바일 친화적.
----------------------
서버(or 오프라인·반응속도 여유): EfficientNet-B0
이유: Top-1 95.4%(최고), 다만 6.21ms라 모바일에서 프레임레이트 최적화가 필요.
----------------------
GhostNet은 정확도는 MNetV3와 비슷하지만 11.43ms로 느리고,
ShuffleNet-V2는 빠르지만 정확도(52.1%)가 부족,
MobileViT-V2는 전반적으로 둘 다 애매.