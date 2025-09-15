# Pland - AI 기반 프로젝트 관리 시스템

현재 개발 중인 백엔드 프로젝트입니다.

## 프로젝트 폴더 구조

```
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

## 기술 스택

- **Backend**: FastAPI
- **Database**: MySQL
- **ML Models**: 탐지기, 분류기, 자연어 모델

## 개발 목표

마지막 프로젝트를 만들어봅시다!

## ⚠️ 환경별 주의사항

### 🏢 피씨방/공용 환경에서 개발 시
- **포트 제한**: 피씨방에서는 개발 포트(8000, 8001 등)가 차단될 수 있습니다
- **네트워크 제한**: AWS RDS 등 외부 데이터베이스 접근이 제한될 수 있습니다
- **해결 방법**: 
  - 다른 포트 사용 (3000, 5000, 8080 등)
  - 로컬 데이터베이스 사용 또는 데이터베이스 연결 우회
  - 집이나 사무실에서 테스트 권장

### 🏠 개인 환경에서 개발 시
- 모든 포트와 네트워크 접근이 자유롭게 가능합니다
- 권장 포트: 8000 (백엔드), 8001 (모델 서버), 8081 (프론트엔드)

## 설치 및 실행

### 가상환경 설정

```cmd
# 최상위 폴더에서
python -m venv venv
cd venv/Scripts
activate
# (이후 venv 환경 활성화)
```

### 의존성 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 백엔드 실행 (개인 환경)
cd backend/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 백엔드 실행 (피씨방 환경 - 포트 변경)
uvicorn main:app --reload --host 127.0.0.1 --port 3000
```

## 프로젝트 상태

- [x] 프로젝트 구조 설정
- [x] 기본 폴더 생성
- [ ] 백엔드 API 개발
- [ ] ML 모델 통합
- [ ] 프론트엔드 개발