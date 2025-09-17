# 🌱 Pland Backend Server

Plant care management system의 백엔드 API 서버입니다.

## ⚠️ 환경별 주의사항

### 🏢 피씨방/공용 환경에서 개발 시

- **포트 제한**: 8000 포트가 차단될 수 있음
- **데이터베이스 연결**: AWS RDS 접근이 제한될 수 있음
- **해결 방법**:
  - 포트 변경: `--port 3000` 또는 `--port 5000`
  - 호스트 변경: `--host 127.0.0.1`
  - 데이터베이스 연결 우회 (임시)

### 🏠 개인 환경에서 개발 시

- 모든 포트와 네트워크 접근 자유
- 권장: `--host 0.0.0.0 --port 8000`

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
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 피씨방/제한된 환경

```bash
cd app
uvicorn main:app --reload --host 127.0.0.1 --port 3000
```

## 📋 서버 정보

- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **포트**: 8000
- **버전**: FastAPI 0.115.6, Python 3.11+

## 🔧 주요 기능

- ✅ **사용자 인증**: JWT 기반 로그인/회원가입
- ✅ **식물 관리**: 식물 등록, 조회, 수정, 삭제
- ✅ **일기 작성**: 식물 관리 일기 CRUD
- ✅ **이미지 업로드**: 식물 사진 업로드 및 관리
- ✅ **대시보드**: 사용자별 식물 현황 요약
- 🔄 **AI 진단**: 식물 건강/해충 진단 (모델 서버 연동)
- 🔄 **날씨 정보**: 식물 관리에 필요한 날씨 데이터

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── routers/             # API 라우터
│   │   ├── auth.py         # 인증 관련 API
│   │   ├── plants.py       # 식물 관리 API
│   │   ├── dashboard.py    # 대시보드 API
│   │   └── images.py       # 이미지 업로드 API
│   ├── services/            # 비즈니스 로직
│   │   ├── auth_service.py # 인증 서비스
│   │   ├── plants_service.py # 식물 관리 서비스
│   │   └── dashboard_service.py # 대시보드 서비스
│   ├── crud/               # 데이터베이스 CRUD
│   ├── models/             # 데이터 모델
│   ├── schemas/            # Pydantic 스키마
│   ├── core/               # 핵심 설정 (DB, Config)
│   ├── ml/                 # 머신러닝 관련 기능
│   └── utils/              # 유틸리티 함수
├── requirements.txt         # Python 의존성 (최신 버전)
└── venv/                    # 가상환경
```

## 🛠️ 개발 환경 설정

1. **Python 3.11+** 설치
2. **가상환경 생성**: `python -m venv venv`
3. **가상환경 활성화**
4. **의존성 설치**: `pip install -r requirements.txt`

## 🔍 문제 해결

- **포트 충돌**: 다른 포트 사용 `--port 8001`
- **의존성 오류**: `pip install --upgrade pip` 후 재설치
- **가상환경 오류**: 가상환경 삭제 후 재생성
- **DB 연결 오류**: `core/config.py`에서 DB 설정 확인

## 📝 API 엔드포인트

- `POST /auth/register` - 회원가입
- `POST /auth/login` - 로그인
- `POST /auth/refresh` - 토큰 갱신
- `GET /plants` - 식물 목록 조회
- `POST /plants` - 식물 등록
- `GET /dashboard` - 대시보드 데이터
- `POST /images/upload` - 이미지 업로드

## 🔗 연동 서비스

- **Models Server**: http://localhost:8001 (AI 진단)
- **Frontend**: React Native (Expo)
- **Database**: MySQL (AWS RDS)
