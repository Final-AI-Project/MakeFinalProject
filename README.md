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
├── README.md                    # 프로젝트 개요 (이 파일)
├── .erd                        # 데이터베이스 ERD
├── sample1.jpg                  # 테스트용 이미지
│
├── backend/                     # 🌐 백엔드 API 서버
│   ├── README.md               # 백엔드 실행 가이드
│   ├── requirements.txt        # Python 의존성 (최신 버전)
│   ├── venv/                   # 가상환경
│   └── app/                    # FastAPI 애플리케이션
│       ├── main.py             # 메인 애플리케이션
│       ├── api/                # API 라우터 (통합)
│       ├── core/               # 핵심 설정 (DB, Config)
│       ├── services/           # 비즈니스 로직
│       ├── repositories/       # 데이터베이스 CRUD
│       ├── models/             # 데이터 모델
│       ├── schemas/            # Pydantic 스키마
│       ├── clients/            # 외부 API 클라이언트
│       ├── static/             # 정적 파일
│       └── utils/              # 유틸리티 함수
│
├── frontend/                    # 📱 React Native 모바일 앱
│   ├── README.md               # 프론트엔드 실행 가이드
│   ├── package.json            # Node.js 의존성 (최신 버전)
│   ├── app.json                # Expo 설정
│   ├── app/                    # Expo Router 앱 구조
│   │   ├── (auth)/             # 인증 화면
│   │   ├── (main)/             # 메인 앱 화면
│   │   ├── (public)/           # 공개 화면
│   │   └── common/             # 공통 컴포넌트
│   ├── assets/                 # 이미지, 폰트 등 리소스
│   ├── constants/              # 상수 정의
│   ├── hooks/                  # 커스텀 훅
│   ├── libs/                   # 라이브러리 및 유틸리티
│   └── types/                  # TypeScript 타입 정의
│
└── models/                      # 🤖 AI 모델 서버
    ├── README.md               # 모델 서버 실행 가이드
    ├── requirements.txt        # ML 의존성 (최신 버전)
    ├── main.py                 # FastAPI 모델 서버
    ├── classifier/             # 식물 분류 모델
    │   ├── cascade/            # 캐스케이드 분류기
    │   └── pestcase/           # 해충 분류기
    ├── detector/               # 잎 탐지 모델
    ├── healthy/                # 건강 상태 모델
    ├── LMM/                    # 대화형 AI 모델
    └── weight/                 # 모델 가중치 저장소
=======
pland/
├─ README.md          # 이 파일
├─ .gitignore         # Git 무시 파일
├─ .env               # 환경 변수 예시
├─ requirements.txt   # 고정된 의존성
├─ models/            # 탐지기, 분류기 파일
│  ├─ weight/         # 가중치
│  ├─ LMM/            # 자연어 모델
│  ├─ classifier/     # 분류 모델
│  └─ detector/       # 탐지 모델
├─ backend/           # FastAPI 백엔드
│  └─ app/
│     ├─ main.py      # FastAPI 엔트리
│     ├─ config.py    # 설정 관리
│     ├─ routers/     # API 라우터
│     ├─ services/    # 비즈니스 로직
│     ├─ ml/          # ML 파이프라인
│     └─ utils/       # 유틸리티(ex. token)
└─ frontend/                                   # React Native + Expo 프론트엔드 루트
   ├─ .expo/                                   # Expo 개발 환경 메타/캐시 디렉터리(자동 생성)
   │  ├─ types/                                # expo-router가 생성하는 타입 선언 폴더
   │  │   └─ router.d.ts                       # 라우트 경로/파라미터에 대한 타입 정의(자동 생성)
   │  ├─ devices.json                          # Expo Dev Tools가 인식한 디바이스/시뮬레이터 정보
   │  └─ README.md                             # expo-router 사용/구조 관련 자동 생성 설명 문서
   ├─ app/                                     # expo-router의 “파일 기반 라우팅” 루트
   │  ├─ (tabs)/                               # 그룹 라우트: 탭 네비게이션 묶음
   │  │   ├─ _layout.tsx                       # 탭 네비게이션 레이아웃(Tabs 설정, 아이콘/라벨 등)
   │  │   ├─ diary.tsx                         # “일기” 탭 화면(사용자 식물 일기/기록 페이지)
   │  │   ├─ explore.tsx                       # 예제/가이드 화면(템플릿 데모 컴포넌트들 사용)
   │  │   ├─ index.tsx                         # 메인(Home) 탭 화면(앱 진입 기본 탭)
   │  │   └─ profile.tsx                       # 프로필 탭 화면(사용자 정보/설정)
   │  ├─ _layout.tsx                           # 앱 전역 레이아웃(Theme, SafeArea, <Slot/> 배치)
   │  ├─ +not-found.tsx                        # 404 대체 화면(정의되지 않은 경로 진입 시 표시)
   │  └─ plant-detail.tsx                      # 식물 상세 페이지(/plant-detail?id=...) 라우트
   ├─ assets/                                  # 정적 리소스(폰트/이미지 등)
   │  ├─ fonts/
   │  │   └─ SpaceMono-Regular.ttf             # 앱에서 로드해 사용하는 TrueType 폰트
   │  └─ images/
   │      ├─ adaptive-icon.png                 # 안드로이드용 Adaptive Icon 원본
   │      ├─ favicon.png                       # 웹 파비콘(Expo Web)
   │      ├─ icon.png                          # 앱 아이콘(기본)
   │      └─ splash-icon.png                   # 스플래시 화면 이미지(런치 스크린)
   ├─ components/                              # 재사용 가능한 UI 컴포넌트 모음
   │  ├─ ui/
   │  │  ├─ IconSymbol.ios.tsx                 # iOS 전용 아이콘 컴포넌트(SF Symbols 등 플랫폼 분기)
   │  │  ├─ IconSymbol.tsx                     # 공통 아이콘 컴포넌트(플랫폼별 구현 분기용 기본)
   │  │  ├─ TabBarBackground.ios.tsx           # iOS 전용 탭바 배경(BlurView 등 iOS UI 적용)
   │  │  └─ TabBarBackground.tsx               # 탭바 배경 공통 버전(플랫폼 공통/웹 대체)
   │  ├─ Collapsible.tsx                       # 접기/펼치기(Accordion) 컴포넌트(애니메이션 포함)
   │  ├─ ExternalLink.tsx                      # 외부 링크 열기용 컴포넌트(Linking/웹 앵커 처리)
   │  ├─ HapticTab.tsx                         # 탭 전환 시 햅틱 피드백 제공 버튼/래퍼
   │  ├─ HelloWave.tsx                         # 인사 이모지/웨이브 애니메이션 데모 컴포넌트
   │  ├─ ParallaxScrollView.tsx                # 패럴랙스 헤더가 있는 스크롤 뷰(헤더 확대/축소 효과)
   │  ├─ ThemedText.tsx                        # 테마 인식 텍스트 컴포넌트(라이트/다크 색상 적용)
   │  └─ ThemedView.tsx                        # 테마 인식 뷰 컴포넌트(배경/경계 색상 자동화)
   ├─ constants/
   │  └─ Colors.ts                             # 라이트/다크 테마 색상 팔레트 상수 정의
   ├─ hooks/
   │  ├─ useColorScheme.ts                     # 시스템 컬러 스킴 감지 훅(iOS/Android 공통)
   │  ├─ useColorScheme.web.ts                 # 웹 전용 컬러 스킴 훅(브라우저 API 대응)
   │  └─ useThemeColor.ts                      # 테마별 색상 선택 로직 훅(컴포넌트에서 호출)
   ├─ node_modules/                            # 프로젝트 의존성 패키지(자동 생성/관리)
   ├─ scripts/
   │  └─ reset-project.js                      # 프로젝트 초기화/캐시 삭제 등 보조 스크립트
   ├─ .gitignore                               # Git에 포함하지 않을 파일/폴더 목록
   ├─ app.json                                 # Expo 앱 설정(name, slug, icon, splash, plugins 등)
   ├─ eslint.config.js                         # ESLint 설정(규칙/플러그인/파서 설정)
   ├─ expo-env.d.ts                            # Expo 전용 타입 선언(환경/전역 타입 보강)
   ├─ package-lock.json                        # 의존성 잠금 파일(NPM 해시/버전 고정)
   ├─ package.json                             # 패키지 메타/스크립트/의존성 정의
   ├─ README.md                                # 프로젝트 개요/실행 방법/폴더 구조 설명 문서
   └─ tsconfig.json                            # TypeScript 컴파일 옵션/경로 별칭 설정
```

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

## 🔄 폴더 구조 변경 요약

### 변경 전/후 비교

**변경 전:**

```
backend/app/
├── routers/          # API 라우터
├── routes/           # 라우터 통합
├── features/         # 기능별 라우터
├── pages/            # 페이지별 라우터
└── static/           # 정적 파일 (분산)
```

**변경 후:**

```
backend/app/
├── api/              # 통합된 API 라우터
│   ├── __init__.py   # 라우터 통합 진입점
│   ├── deps.py       # 공통 의존성
│   └── *.py          # 리소스별 라우터
├── services/         # 비즈니스 로직
├── repositories/     # 데이터베이스 CRUD
└── static/           # 정적 파일 (통합)
```

### 이동 규칙

- `routers/` + `routes/` + `features/` + `pages/` → `api/`
- `static/` (루트) + `static/` (app) → `app/static/` (통합)
- 빈 폴더 삭제: `crud/`, `ml/`

### Import 치환 규칙

```python
# 변경 전
from app.routers import X
from app.routes import X
from app.features import X
from app.pages import X

# 변경 후
from app.api import X
```

### 기동/테스트 확인 방법

```bash
# 백엔드 서버 실행
cd backend/app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 3000

# 헬스체크
curl http://localhost:3000/health

# API 문서 확인
http://localhost:3000/docs
```

## 📊 프로젝트 진행 상황

### ✅ 완료된 기능

- [x] 프로젝트 구조 설정
- [x] 백엔드 API 기본 구조
- [x] 사용자 인증 시스템
- [x] 데이터베이스 스키마
- [x] AI 모델 서버 기본 구조
- [x] 프론트엔드 기본 화면
- [x] 의존성 최신 버전 업데이트

### 🔄 개발 중인 기능

- [ ] 식물 관리 CRUD API
- [ ] AI 진단 API 연동
- [ ] 이미지 업로드 기능
- [ ] 대시보드 데이터 API
- [ ] 프론트엔드 화면 완성

### 📋 예정된 기능

- [ ] 식물 관리 일기
- [ ] 날씨 정보 연동
- [ ] 푸시 알림
- [ ] 소셜 기능
- [ ] 관리 통계 및 분석

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
