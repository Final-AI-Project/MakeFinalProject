# Backend Server 실행 가이드

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

## 🔧 주요 기능
- 사용자 인증 및 관리
- 식물 정보 관리
- 일기 작성 및 관리
- 이미지 업로드 및 처리
- 대시보드 데이터 제공

## 📁 프로젝트 구조
```
backend/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── routers/             # API 라우터
│   ├── services/            # 비즈니스 로직
│   ├── db/                  # 데이터베이스 모델 및 CRUD
│   ├── ml/                  # 머신러닝 관련 기능
│   └── utils/               # 유틸리티 함수
├── requirements.txt         # Python 의존성
└── venv/                    # 가상환경
```

## 🛠️ 개발 환경 설정
1. Python 3.8+ 설치
2. 가상환경 생성: `python -m venv venv`
3. 가상환경 활성화
4. 의존성 설치: `pip install -r requirements.txt`

## 🔍 문제 해결
- **포트 충돌**: 다른 포트 사용 `--port 8001`
- **의존성 오류**: `pip install --upgrade pip` 후 재설치
- **가상환경 오류**: 가상환경 삭제 후 재생성
