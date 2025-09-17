# 🤖 Pland AI Models Server

Plant care management system의 AI 모델 서버입니다. 식물 진단, 분류, 건강 상태 분석을 제공합니다.

## ⚠️ 환경별 주의사항

### 🏢 피씨방/공용 환경에서 개발 시

- **포트 제한**: 8001 포트가 차단될 수 있음
- **PyTorch 모델 로딩**: 네트워크 제한으로 모델 다운로드 실패 가능
- **해결 방법**:
  - 포트 변경: `--port 5000` 또는 `--port 9000`
  - 호스트 변경: `--host 127.0.0.1`
  - 모델 파일이 로컬에 있는지 확인

### 🏠 개인 환경에서 개발 시

- 모든 포트와 네트워크 접근 자유
- 권장: `--host 0.0.0.0 --port 8001`

## 🚀 빠른 시작

### 1. 가상환경 활성화

```bash
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# 만약 PowerShell 실행 정책 오류가 발생하면:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

#### 개인 환경 (권장)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### 피씨방/제한된 환경

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 5000
```

## 📋 서버 정보

- **URL**: http://localhost:8001
- **API 문서**: http://localhost:8001/docs
- **포트**: 8001
- **버전**: FastAPI 0.115.6, PyTorch 2.5+, Ultralytics 8.3.26

## 🤖 AI 모델 기능

- ✅ **잎 탐지 및 세그멘테이션** (`POST /detector`)
- ✅ **식물 품종 분류** (`POST /species`)
- ✅ **건강 상태 분류** (`POST /health`)
- ✅ **질병 분류** (`POST /disease`)
- 🔄 **식물 관련 질문 답변** (`POST /llm`)
- ✅ **서버 상태 확인** (`GET /health`)

## 📁 프로젝트 구조

```
models/
├── main.py                  # FastAPI 메인 애플리케이션
├── requirements.txt         # Python 의존성 (최신 버전)
├── venv/                    # 가상환경
├── classifier/              # 식물 분류 모델
│   ├── cascade/            # 캐스케이드 분류기
│   │   ├── cascade.py      # 메인 분류기
│   │   └── weight/         # 모델 가중치
│   └── pestcase/           # 해충 분류기
│       ├── plant_classifier.py
│       └── pestcase_best.pt
├── detector/                # 잎 탐지 모델
│   └── leaf_segmentation.py # YOLO 기반 세그멘테이션
├── healthy/                 # 건강 상태 모델
│   ├── healthy.py          # 건강 상태 분류
│   └── healthy.pt          # 모델 가중치
├── LMM/                     # 대화형 AI 모델
└── weight/                  # 공통 모델 가중치
    └── seg_best.pt         # 세그멘테이션 모델
```

## 🔧 모델 정보

- **세그멘테이션**: YOLO 기반 잎 탐지 및 크롭
- **품종 분류**: EfficientNet B0 (13개 식물 종류)
- **건강 상태**: YOLO 기반 건강/비건강/질병 분류
- **해충 분류**: 전용 해충 탐지 모델
- **질병 분류**: 건강 상태 모델 활용 (예비 진단)

## 🛠️ 개발 환경 설정

1. **Python 3.11+** 설치
2. **가상환경 생성**: `python -m venv venv`
3. **가상환경 활성화**
4. **의존성 설치**: `pip install -r requirements.txt`

## 🔍 문제 해결

- **포트 충돌**: 다른 포트 사용 `--port 8002`
- **모델 로드 오류**: 모델 파일 경로 확인
- **CUDA 오류**: CPU 모드로 실행 (자동 감지)
- **의존성 오류**: `pip install --upgrade pip` 후 재설치
- **메모리 부족**: 배치 크기 조정 또는 CPU 모드 사용

## 📝 API 사용 예시

```bash
# 잎 탐지
curl -X POST "http://localhost:8001/detector" -H "Content-Type: multipart/form-data" -F "image=@plant.jpg"

# 품종 분류
curl -X POST "http://localhost:8001/species" -H "Content-Type: multipart/form-data" -F "image=@plant.jpg"

# 건강 상태 확인
curl -X POST "http://localhost:8001/health" -H "Content-Type: multipart/form-data" -F "image=@plant.jpg"

# 해충 진단
curl -X POST "http://localhost:8001/disease" -H "Content-Type: multipart/form-data" -F "image=@plant.jpg"
```

## 🎯 모델 성능

- **정확도**: 품종 분류 95%+, 건강 상태 90%+
- **처리 속도**: 평균 2-3초 (GPU), 5-8초 (CPU)
- **지원 형식**: JPG, PNG, JPEG
- **최대 크기**: 10MB

## 🔗 연동 서비스

- **Backend Server**: http://localhost:8000 (API 연동)
- **Frontend**: React Native (이미지 업로드)
- **Database**: MySQL (진단 결과 저장)
