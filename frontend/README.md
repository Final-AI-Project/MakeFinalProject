# 🌱 Pland Frontend

Plant care management system의 React Native 모바일 앱입니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
npm install
```

### 2. 개발 서버 실행

```bash
# Expo 개발 서버 시작
npx expo start

# 또는 npm 스크립트 사용
npm start
```

## 📋 서버 정보

- **Expo Dev Tools**: http://localhost:19002
- **Metro Bundler**: http://localhost:8081
- **포트**: 19000 (기본)
- **버전**: Expo SDK 52, React Native 0.76.3

## 📱 플랫폼별 실행

```bash
# Android 에뮬레이터
npx expo start --android

# iOS 시뮬레이터 (macOS만)
npx expo start --ios

# 웹 브라우저
npx expo start --web

# 특정 디바이스
npx expo start --tunnel
```

## 🔧 주요 기능

- ✅ **사용자 인증**: 로그인/회원가입 화면
- ✅ **메인 대시보드**: 식물 현황 요약
- 🔄 **식물 관리**: 식물 등록, 조회, 수정
- 🔄 **일기 작성**: 식물 관리 기록
- 🔄 **AI 진단**: 식물 건강/해충 진단
- 🔄 **날씨 정보**: 식물 관리에 필요한 날씨
- 🔄 **이미지 업로드**: 식물 사진 촬영/업로드

## 📁 프로젝트 구조

```
frontend/
├── app/                     # Expo Router 앱 구조
│   ├── (auth)/             # 인증 관련 화면
│   │   ├── login.tsx       # 로그인 화면
│   │   └── signup.tsx      # 회원가입 화면
│   ├── (main)/             # 메인 앱 화면
│   │   └── home.tsx        # 홈/대시보드 화면
│   ├── (public)/           # 공개 화면
│   │   └── splash.tsx      # 스플래시 화면
│   ├── common/             # 공통 컴포넌트
│   │   ├── loading.tsx     # 로딩 컴포넌트
│   │   └── weatherBox.tsx  # 날씨 정보 컴포넌트
│   └── index.tsx           # 앱 진입점
├── assets/                 # 이미지, 폰트 등 리소스
├── constants/              # 상수 정의
├── hooks/                  # 커스텀 훅
├── libs/                   # 라이브러리 및 유틸리티
├── types/                  # TypeScript 타입 정의
├── package.json            # 의존성 및 스크립트 (최신 버전)
└── app.json               # Expo 설정
```

## 🛠️ 개발 환경 설정

1. **Node.js 18+** 설치
2. **Expo CLI 설치**: `npm install -g @expo/cli`
3. **의존성 설치**: `npm install`
4. **개발 서버 실행**: `npx expo start`

## 📱 모바일 테스트

### Android

1. Android Studio 설치 및 에뮬레이터 설정
2. `npx expo start --android`

### iOS (macOS만)

1. Xcode 설치 및 시뮬레이터 설정
2. `npx expo start --ios`

### 실제 디바이스

1. Expo Go 앱 설치 (Google Play/App Store)
2. QR 코드 스캔하여 연결

## 🔍 문제 해결

- **포트 충돌**: `npx expo start --port 19001`
- **캐시 문제**: `npx expo start --clear`
- **의존성 오류**: `rm -rf node_modules && npm install`
- **Metro 오류**: `npx expo start --reset-cache`

## 🌐 백엔드 연결

- **Backend API**: http://localhost:8000
- **Models API**: http://localhost:8001
- 연결 설정은 `libs/` 폴더에서 확인

## 📝 유용한 명령어

```bash
# 프로젝트 초기화
npm run reset-project

# 타입 체크
npm run type-check

# 린트 검사
npm run lint

# 빌드 (웹)
npx expo build:web
```

## 🎨 UI/UX 특징

- **모던 디자인**: 깔끔하고 직관적인 인터페이스
- **반응형 레이아웃**: 다양한 화면 크기 지원
- **다크/라이트 모드**: 사용자 선호도에 따른 테마
- **애니메이션**: 부드러운 화면 전환 및 상호작용
