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

### ✅ **완전 구현된 기능들**

#### 🔐 **사용자 인증 시스템**

- JWT 기반 로그인/회원가입
- 토큰 갱신 및 블랙리스트 관리
- 사용자 프로필 관리

#### 🌱 **식물 관리 시스템**

- 식물 등록, 조회, 수정, 삭제
- 식물별 상세 정보 관리
- 사용자별 식물 목록 조회

#### 📝 **일기 작성/수정 시스템** (NEW!)

- 일기 작성 (제목, 내용, 식물별명, 해시태그)
- 사진 업로드 지원
- 날씨 자동 입력
- AI 식물 답변 자동 생성
- 일기 수정시 AI 답변 재생성
- 일기 목록 조회 및 검색

#### 🖼️ **이미지 관리 시스템**

- 식물 사진 업로드 및 관리
- 일기 사진 첨부
- 이미지 URL 생성 및 저장

#### 📊 **대시보드 시스템**

- 사용자별 식물 현황 요약
- 일기 통계 정보
- 식물별 관리 현황

#### 🤖 **AI 기능들**

- 식물 건강 진단 (모델 서버 연동)
- 해충 진단 (모델 서버 연동)
- 식물 종류 분류
- 물주기 예측
- **식물 LLM 답변 생성** (NEW!)

#### 🌤️ **날씨 정보 시스템**

- 현재 날씨 정보 자동 입력
- 날씨 아이콘 및 상태 제공

#### 💧 **물주기 관리**

- 물주기 기록 관리
- 물주기 예측 및 알림

### 🔄 **모델 서버 연동 기능들**

- 식물 건강 상태 분류
- 해충 진단 및 치료법 제안
- 식물 종류 자동 인식
- 물주기 스케줄 예측

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

### 🔐 **인증 관련**

- `POST /auth/register` - 회원가입
- `POST /auth/login` - 로그인
- `POST /auth/refresh` - 토큰 갱신
- `POST /auth/logout` - 로그아웃

### 🌱 **식물 관리** (NEW!)

- `POST /plants/classify-species` - 이미지로 품종 분류
- `POST /plants` - 식물 등록 (이미지 업로드 + 품종 분류 지원)
- `GET /plants` - 식물 목록 조회 (페이지네이션 지원)
- `GET /plants/search` - 식물 검색
- `GET /plants/stats` - 식물 통계 정보
- `GET /plants/{plant_idx}` - 식물 상세 정보
- `PUT /plants/{plant_idx}` - 식물 정보 수정
- `DELETE /plants/{plant_idx}` - 식물 삭제
- `POST /plants/{plant_idx}/reclassify` - 식물 품종 재분류

### 📝 **일기 관리** (NEW!)

- `POST /diary/create` - 일기 작성 (사진 업로드 지원)
- `GET /diary/{diary_id}` - 일기 조회
- `PUT /diary/{diary_id}` - 일기 수정
- `DELETE /diary/{diary_id}` - 일기 삭제
- `GET /diary-list` - 일기 목록 조회 (날짜/식물별 정렬, 필터링 지원)
- `GET /diary-list/search` - 일기 내용 검색
- `GET /diary-list/stats` - 일기 통계 정보
- `GET /diary-list/plants/summary` - 식물별 일기 요약
- `GET /diary-list/recent` - 최근 일기 조회
- `GET /diary-list/export` - 일기 내보내기 (JSON/CSV)

### 🖼️ **이미지 관리**

- `POST /images/upload` - 일반 이미지 업로드
- `POST /plant-detail/{plant_idx}/upload-image` - 식물 사진 업로드
- `GET /images/{image_id}` - 이미지 조회
- `DELETE /images/{image_id}` - 이미지 삭제

### 📊 **대시보드 & 통계**

- `GET /dashboard` - 대시보드 데이터
- `GET /dashboard/stats` - 사용자 통계 정보

### 🤖 **AI 기능**

- `POST /ai/plant-health` - 식물 건강 진단
- `POST /ai/pest-diagnosis` - 해충 진단
- `POST /ai/species-classification` - 식물 종류 분류
- `POST /ai/watering-prediction` - 물주기 예측
- `POST /plant-chat` - 식물과 대화 (LLM)

### 🏥 **병충해 진단 관리** (NEW!)

- `GET /medical/diagnoses` - 병충해 진단 목록 조회 (이미지 포함)
- `GET /medical/diagnoses/{diagnosis_id}` - 병충해 진단 상세 정보
- `POST /medical/diagnoses` - 병충해 진단 기록 생성
- `POST /medical/diagnoses/with-image` - 이미지와 함께 병충해 진단 기록 생성
- `PUT /medical/diagnoses/{diagnosis_id}` - 병충해 진단 기록 수정
- `DELETE /medical/diagnoses/{diagnosis_id}` - 병충해 진단 기록 삭제
- `GET /medical/stats` - 병충해 진단 통계
- `GET /medical/diagnoses/plant/{plant_id}` - 특정 식물의 진단 기록

### 💧 **물주기 관리**

- `GET /plant-detail/{plant_idx}/watering-records` - 물주기 기록 조회
- `POST /plant-detail/{plant_idx}/watering-records` - 물주기 기록 추가
- `GET /watering/prediction` - 물주기 예측

### 🌤️ **날씨 정보**

- `GET /weather/current` - 현재 날씨 정보

### 📚 **정보방 페이지** (NEW!)

- `GET /info-room/plants` - 식물 위키 목록 조회 (검색/페이지네이션 지원)
- `GET /info-room/plants/{wiki_plant_id}` - 식물 위키 상세 정보
- `GET /info-room/pests` - 병충해 위키 목록 조회 (검색/페이지네이션 지원)
- `GET /info-room/pests/{pest_id}` - 병충해 위키 상세 정보
- `GET /info-room/stats` - 정보방 통계 정보
- `GET /info-room/plants/category/{category}` - 카테고리별 식물 조회
- `GET /info-room/search` - 식물 위키 통합 검색

## 🔗 연동 서비스

- **Models Server**: http://localhost:8001 (AI 진단, LLM 답변)
- **Frontend**: React Native (Expo)
- **Database**: MySQL (AWS RDS)
- **Weather API**: 날씨 정보 자동 입력
- **Image Storage**: 로컬 파일 시스템

## 🆕 **최근 추가된 기능들**

### 📝 **일기 작성/수정 시스템**

- 사용자가 일기를 작성하면 AI가 식물의 관점에서 답변 생성
- 사진 업로드, 날씨 자동 입력, 해시태그 지원
- 일기 수정시 AI 답변이 새로운 내용에 맞춰 재생성
- 식물별 맞춤형 답변 (몬스테라, 선인장, 호접란 등 10종 지원)

### 🤖 **식물 LLM 답변 시스템**

- 일기 내용에 따른 자동 답변 생성
- 식물의 성격에 맞는 톤앤매너
- 일상/식물관리/하이브리드 모드 자동 감지
- 실용적인 조언과 공감 제공

### 🌤️ **날씨 자동 입력**

- 일기 작성시 현재 날씨 정보 자동 입력
- 날씨 상태와 아이콘 URL 제공
- 수정시 새로운 날씨 정보로 업데이트

## 🚀 **사용 가능한 모든 기능 요약**

현재 백엔드에서 **완전히 구현되어 사용 가능한** 기능들:

1. ✅ **사용자 인증** (회원가입, 로그인, 토큰 관리)
2. ✅ **식물 관리** (등록, 조회, 수정, 삭제)
3. ✅ **일기 시스템** (작성, 수정, 조회, 삭제, 검색)
4. ✅ **AI 답변** (식물 LLM 답변 자동 생성)
5. ✅ **정보방 시스템** (식물/병충해 위키 조회, 카테고리별 검색)
6. ✅ **이미지 관리** (업로드, 저장, 조회)
7. ✅ **대시보드** (통계, 현황 요약)
8. ✅ **날씨 정보** (자동 입력)
9. ✅ **물주기 관리** (기록, 예측)
10. ✅ **AI 진단** (건강, 해충, 종류 분류)
11. ✅ **식물 대화** (LLM 기반 대화)
