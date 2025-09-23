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
- ✅ **메인 대시보드**: 식물 현황 요약 + 습도 아치형 바
- ✅ **식물 관리**: 식물 등록, 조회, 수정, 삭제
- ✅ **일기 작성**: 식물 관리 기록 + AI 답변
- ✅ **AI 진단**: 식물 건강/해충 진단 + 이미지 저장
- ✅ **날씨 정보**: 식물 관리에 필요한 날씨
- ✅ **이미지 업로드**: 식물 사진 촬영/업로드
- ✅ **습도 모니터링**: 실시간 습도 데이터 시각화
- ✅ **병충해 진단**: 이미지 업로드, 진단 결과 저장

## 📁 프로젝트 구조

```
frontend/
├── app/                     # Expo Router 앱 구조
│   ├── (auth)/             # 인증 관련 화면
│   │   ├── login.tsx       # 로그인 화면
│   │   └── signup.tsx      # 회원가입 화면
│   ├── (page)/             # 메인 앱 화면
│   │   ├── home.tsx        # 홈/대시보드 화면 (습도 아치형 바)
│   │   ├── medical.tsx     # 병충해 진단 목록
│   │   ├── diaryList.tsx   # 일기 목록
│   │   └── (stackless)/    # 스택리스 화면들
│   │       ├── plant-detail.tsx    # 식물 상세
│   │       ├── plant-new.tsx       # 식물 등록
│   │       ├── medical-detail.tsx  # 병충해 진단
│   │       ├── diary.tsx           # 일기 작성
│   │       └── info-room.tsx       # 정보방
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

- **Backend API**: http://localhost:8000 (또는 3000)
- **Models API**: http://localhost:5000 (또는 8001)
- **환경 변수**: `.env` 파일에서 `EXPO_PUBLIC_API_BASE_URL` 설정
- 연결 설정은 `libs/` 폴더에서 확인

## 🆕 **최근 추가된 기능들**

### 💧 **습도 모니터링 시스템** (NEW!)

- **메인페이지 아치형 바**: 각 식물의 최근 습도를 시각적으로 표시
- **실시간 데이터**: 백엔드에서 습도 데이터를 가져와 아치형 바에 반영
- **기본값 처리**: 습도 데이터가 없는 식물은 50%로 표시
- **시각적 피드백**: 습도에 따른 아치형 바 색상 및 채움 정도

### 🏥 **병충해 진단 시스템** (ENHANCED!)

- **이미지 업로드**: 진단할 식물 사진 촬영/업로드
- **진단 결과**: 상위 3개 진단 결과 표시
- **건강 상태 처리**: 건강한 진단 결과는 저장하지 않음
- **등록 버튼**: 건강한 상태일 때 비활성화
- **아코디언 UI**: 진단 목록에서 펼치기 전/후 모두 이미지 정상 표시
- **이미지 저장**: 진단 이미지가 정상적으로 저장되고 표시됨

### 📝 **일기 작성 시스템** (ENHANCED!)

- **AI 답변**: 식물의 관점에서 자동 답변 생성
- **사진 업로드**: 일기와 함께 사진 첨부
- **날씨 정보**: 외부 기상청 API 연동
- **해시태그**: 일기 분류 및 검색 지원
- **식물별 맞춤**: 각 식물의 성격에 맞는 답변

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
