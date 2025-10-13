# 🌱 Pland - AI 기반 식물 관리 시스템

AI를 활용한 스마트 식물 관리 플랫폼입니다. 식물 진단, 건강 상태 분석, 관리 일기 작성 등 종합적인 식물 케어 서비스를 제공합니다.

## 🎯 프로젝트 개요

**Pland**는 사용자가 키우는 식물의 건강 상태를 AI로 진단하고, 체계적인 관리 방법을 제안하는 모바일 애플리케이션입니다.

### 주요 기능

- 🤖 **AI 식물 진단**: 사진 촬영으로 식물 품종, 건강 상태, 해충 여부 진단
- 📱 **모바일 앱**: React Native + Expo로 개발된 크로스 플랫폼 앱
- 🔐 **사용자 인증**: JWT 기반 안전한 로그인/회원가입 시스템
- 📊 **대시보드**: 사용자별 식물 현황 및 관리 통계
- 📝 **관리 일기**: 식물별 상세한 관리 기록 및 히스토리
- 🌤️ **날씨 연동**: 식물 관리에 필요한 날씨 정보 제공

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Models     │
│   (React Native)│◄──►│   (FastAPI)     │◄──►│   (PyTorch)     │
│   Port: 19000   │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Expo Dev      │    │   MySQL DB      │    │   Model Weights │
│   Tools         │    │   (AWS RDS)     │    │   (Local)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 프로젝트 구조

```
Pland_predev2/
├── Final.sql                                  # MySQL 스키마 정의(기준 문서)
├── backend/                                   # FastAPI 백엔드 루트
│   ├── app/
│   │   ├── main.py                            # FastAPI 엔트리 포인트
│   │   ├── core/                              # 전역 설정/환경(config)
│   │   ├── db/                                # 커넥션 풀, 트랜잭션 유틸
│   │   ├── clients/                           # 외부 API 클라이언트(httpx 등)
│   │   ├── features/                          # API 엔드포인트(라우트/핸들러)
│   │   ├── models/                            # 내부 도메인 모델(데이터 구조)
│   │   ├── repositories/                      # DB 접근 레이어(aiomysql 쿼리)
│   │   ├── schemas/                           # Pydantic 스키마(입출력 검증)
│   │   ├── services/                          # 비즈니스 로직(도메인 서비스)
│   │   ├── pages/                             # 페이지 조립(대시보드 등)
│   │   └── utils/                             # 공통 유틸리티(보안, 이미지 등)
│   ├── requirements.txt                       # 백엔드 의존성
│   └── static/                                # 정적 파일(업로드 이미지 등)
├── frontend/                                  # React Native + Expo 앱
│   ├── app/                                   # 파일 기반 라우팅(entry/screens)
│   ├── components/                            # 공용 UI 컴포넌트
│   ├── config/                                # API 설정 등 클라이언트 설정
│   ├── constants/                             # 색상/상수 정의
│   ├── hooks/                                 # 커스텀 훅
│   ├── libs/                                  # 인증/분류 등 라이브러리 래퍼
│   ├── assets/                                # 이미지/폰트 등 정적 리소스
│   ├── package.json
│   └── tsconfig.json
├── models/                                    # AI 모델 서버/가중치
│   ├── main.py                                # 모델 서버 FastAPI 엔트리
│   ├── classifier/                            # 식물/해충 분류 관련
│   │   ├── cascade/
│   │   └── pestcase/
│   ├── detector/                              # 잎/객체 탐지
│   ├── healthy/                               # 건강 상태 모델
│   ├── humidity/                              # 습도 예측 모델
│   └── llm/                                   # LLM 연동 코드
└── README.md
```

백엔드 서브폴더 설명

- core: 애플리케이션 전역 설정 및 환경 변수 로딩
- db: 커넥션 풀 관리, 트랜잭션 헬퍼
- clients: 외부 서비스 연동(httpx 기반 클라이언트)
- repositories: SQL 실행을 통한 데이터 접근 계층
- schemas: 요청/응답 검증용 Pydantic 모델
- services: 도메인 비즈니스 로직 구현
- features: 실제 API 라우터/핸들러 정의
- pages: 대시보드/페이지 단위 조립 로직
- utils: 보안, 이미지 저장 등 공용 유틸

프론트엔드 서브폴더 설명

- app: 라우팅과 화면 엔트리 구성(Expo Router)
- components: 재사용 UI 컴포넌트
- config: API 베이스 URL 등 환경 설정 래퍼
- constants: 색상/문구 등 상수
- hooks: 공용 커스텀 훅
- libs: 인증/분류 요청 등 클라이언트 로직 래퍼
- assets: 이미지/폰트 등 정적 리소스

모델 서버 서브폴더 설명

- classifier: 식물/해충 분류 모델 및 가중치
- detector: 잎/객체 탐지 로직
- healthy: 건강 상태 판별 모델
- humidity: 습도 예측 파이프라인
- llm: 대화형 모델(LLM) 연동 코드

## 🛠️ 기술 스택

### Backend

- **Framework**: FastAPI 0.115.6
- **Database**: MySQL (AWS RDS)
- **Authentication**: JWT + bcrypt
- **ORM**: aiomysql (비동기 MySQL)
- **Python**: 3.11+

### Frontend

- **Framework**: React Native 0.76.3
- **Platform**: Expo SDK 52
- **Navigation**: Expo Router
- **Language**: TypeScript
- **Node.js**: 18+

### AI Models

- **Framework**: PyTorch 2.5+
- **Computer Vision**: Ultralytics 8.3.26, OpenCV 4.10
- **Models**: YOLO, EfficientNet
- **Libraries**: scikit-learn, albumentations

## 🚀 빠른 시작

### 0. 환경 변수 설정

각 서버를 실행하기 전에 환경 변수 파일을 설정해야 합니다:

#### 백엔드 환경 변수

```bash
# backend/.env 파일 생성
cd backend
touch .env  # Windows: type nul > .env
```

`.env` 파일 내용:

```bash
# 데이터베이스 설정
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=your-database-name

# JWT 설정
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API 설정
API_HOST=0.0.0.0
API_PORT=8000

# MQTT 설정 (선택사항)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
```

#### 프론트엔드 환경 변수

```bash
# frontend/.env 파일 생성
cd frontend
touch .env  # Windows: type nul > .env
```

`.env` 파일 내용:

```bash
# API 서버 주소 (IP 주소를 실제 환경에 맞게 변경)
EXPO_PUBLIC_API_BASE_URL="http://192.168.0.7:8000"
```

#### AI 모델 서버 환경 변수

```bash
# models/.env 파일 생성
cd models
touch .env  # Windows: type nul > .env
```

`.env` 파일 내용:

```bash
# 모델 서버 설정
API_HOST=0.0.0.0
API_PORT=8001
MODEL_PATH=./weight

# 모델 파일 경로
CLASSIFIER_MODEL_PATH=./classifier/cascade/weight/plant_classifier.pth
PEST_MODEL_PATH=./pestcase/pest_classifier.pt
HEALTHY_MODEL_PATH=./healthy/healthy.pt
```

### 1. 백엔드 서버 실행

```bash
cd backend
venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. AI 모델 서버 실행

```bash
cd models
venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 3. 프론트엔드 앱 실행

```bash
cd frontend
npm install
npx expo start
```

## 📋 서비스 정보

| 서비스      | URL                        | 포트  | 상태 |
| ----------- | -------------------------- | ----- | ---- |
| Backend API | http://localhost:8000      | 8000  | ✅   |
| AI Models   | http://localhost:8001      | 8001  | ✅   |
| Frontend    | http://localhost:19000     | 19000 | ✅   |
| API Docs    | http://localhost:8000/docs | -     | ✅   |

## ⚠️ 환경별 주의사항

### 🏢 피씨방/공용 환경

- **포트 제한**: 8000, 8001 포트 차단 가능
- **해결책**: `--port 3000` 또는 `--port 5000` 사용
- **네트워크**: AWS RDS 접근 제한 가능

### 🏠 개인 환경

- **권장 설정**: 모든 포트 자유 사용
- **최적 성능**: GPU 가속 AI 모델 실행 가능

### 📶 새로운 와이파이 환경에서 IP 주소 변경

새로운 와이파이 환경으로 변경할 때는 다음 단계를 따라주세요:

#### 1. 현재 IP 주소 확인

```bash
# Windows
ipconfig

# macOS/Linux
ifconfig
```

#### 2. 환경 변수 파일 수정

각 폴더에 `.env` 파일을 생성하거나 수정합니다:

**프로젝트 루트 (선택사항)**

```bash
# 프로젝트 루트/.env
EXPO_PUBLIC_API_BASE_URL="192.168.0.7:3000"
```

**백엔드 폴더**

```bash
# backend/.env
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=your-database-name
JWT_SECRET_KEY=your-jwt-secret-key
```

**프론트엔드 폴더**

```bash
# frontend/.env
EXPO_PUBLIC_API_BASE_URL="192.168.0.7:3000"
```

**AI 모델 서버 폴더**

```bash
# models/.env
MODEL_PATH=./weight
API_HOST=0.0.0.0
API_PORT=8001
```

#### 3. 백엔드 서버 재시작

```bash
cd backend/app
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

#### 4. 프론트엔드 앱 재시작

```bash
cd frontend
npx expo start --clear
```

#### 5. 모바일 앱에서 테스트

- Expo Go 앱에서 QR 코드 스캔
- 네트워크 연결 상태 확인
- API 호출 테스트

#### 💡 주의사항

- **IP 주소**: `192.168.x.x` 형태의 로컬 네트워크 IP 사용
- **포트**: 백엔드와 프론트엔드가 같은 포트를 사용하는지 확인
- **방화벽**: Windows 방화벽에서 해당 포트 허용 필요할 수 있음
- **캐시**: 변경 후 `--clear` 옵션으로 캐시 삭제 권장
- **환경 변수**: `.env` 파일은 Git에 커밋하지 마세요 (보안상 중요)
- **파일 위치**: 각 폴더(`backend/`, `frontend/`, `models/`)에 해당하는 `.env` 파일 생성

## 📊 프로젝트 진행 상황

### ✅ 완료된 기능

- 프로젝트 구조 설정
- 백엔드 API 기본 구조
- 사용자 인증 시스템
- 데이터베이스 스키마
- AI 모델 서버 기본 구조
- 프론트엔드 기본 화면
- 의존성 최신 버전 업데이트
- README 프로젝트 구조 섹션 정리
- 서브폴더 역할 문서화
- 식물 관리 일기

### 🔄 개발 중인 기능

- 식물 관리 CRUD API
- AI 진단 API 연동
- 이미지 업로드 기능
- 대시보드 데이터 API
- 프론트엔드 화면 완성

### 📋 예정된 기능

- 날씨 정보 연동
- 푸시 알림
- 소셜 기능
- 관리 통계 및 분석

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 이슈를 생성해 주세요.

---

**🌱 Pland와 함께 스마트한 식물 관리의 새로운 경험을 시작하세요!**
