# Pland - AI 기반 프로젝트 관리 시스템

AI 기반 프로젝트 관리 시스템의 프론트엔드 (React Native Expo) 및 백엔드 (FastAPI) 프로젝트입니다.

## 프로젝트 구조

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
└─ frontend/          # React Native Expo 프론트엔드
    ├─ app/           # 앱 라우팅
    ├─ components/    # 재사용 가능한 컴포넌트
    ├─ constants/     # 상수 정의
    ├─ hooks/         # 커스텀 훅
    └─ assets/        # 이미지, 폰트 등
```

## 기술 스택

- **Frontend**: React Native, Expo, TypeScript
- **Backend**: FastAPI
- **Database**: SQLite / MongoDB / MySQL (선택 예정)
- **ML Models**: 탐지기, 분류기, 자연어 모델

## 개발 목표

마지막 프로젝트를 만들어봅시다!

## 프론트엔드 실행

1. 의존성 설치

   ```bash
   npm install
   ```

2. 앱 시작

   ```bash
   npx expo start
   ```

## 백엔드 실행

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

# 백엔드 실행
cd backend
uvicorn app.main:app --reload
```

## 프로젝트 상태

- [x] 프로젝트 구조 설정
- [x] 기본 폴더 생성
- [x] 프론트엔드 기본 구조 (React Native Expo)
- [ ] 백엔드 API 개발
- [ ] ML 모델 통합
- [ ] 프론트엔드-백엔드 연동
