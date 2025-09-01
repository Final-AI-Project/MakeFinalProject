# Plant Whisperer (식물 스피킹 진단 웹앱)

식물 사진을 업로드하면 품종을 추정하고 병충해 유무/유형을 분석하여 **식물이 주인에게 말을 건네듯** 자연어로 결과를 전달하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **식물 품종 추정**: 업로드된 이미지에서 식물 품종을 자동으로 분류
- **병충해 진단**: 식물의 건강 상태와 질병 유형을 분석
- **자연어 결과**: 식물이 1인칭으로 다정하게 말하는 방식으로 결과 전달
- **학습 기능**: 사용자 데이터로 모델을 추가 학습 가능
- **100% 무료**: 모든 구성 요소가 오픈소스 라이선스 사용

## 🏗️ 아키텍처

- **Frontend**: React 18 + Vite + TailwindCSS + Zustand + TanStack Query
- **Backend**: FastAPI + Uvicorn + Python 3.11.9
- **ML Pipeline**: U²-Net (전처리) + EfficientNet/ConvNeXt (분류) + ONNX Runtime (추론)
- **NLG**: Jinja2 템플릿 기반 자연어 생성 (로컬 LLM 옵션)

## 📋 시스템 요구사항

- **Node.js**: 20.x LTS
- **Python**: 3.11.9
- **OS**: Windows, macOS, Linux (로컬 또는 단일 VM)
- **메모리**: 최소 4GB RAM (모델 로딩용)
- **저장공간**: 최소 2GB (모델 가중치 및 샘플 데이터)

## 🚀 빠른 시작

### 요구사항 확인

- Python 3.11.9 이상
- Node.js 20.x LTS 이상
- 최소 4GB RAM

### 5분 만에 실행하기

```bash
# 1. 저장소 클론
git clone <repository-url>
cd plant-whisperer

# 2. Python 환경 설정 (Windows)
scripts\setup_python_venv.bat

# 3. 프론트엔드 설정
cd frontend && npm install && cd ..

# 4. 애플리케이션 실행
# 터미널 1: 백엔드
cd backend && uvicorn app.main:app --reload --port 8000

# 터미널 2: 프론트엔드
cd frontend && npm run dev

# 5. 브라우저에서 접속
# http://localhost:5173
```

## 🛠️ 상세 설치 및 실행

### 1. 저장소 클론 및 초기화

```bash
git clone <repository-url>
cd plant-whisperer
```

### 2. Python 환경 설정

```bash
# Windows
scripts\setup_python_venv.bat

# Linux/macOS
bash scripts/setup_python_venv.sh
```

**또는 수동으로:**

```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/macOS)
source venv/bin/activate

# 의존성 설치
pip install -r backend/requirements.txt
```

### 3. 프론트엔드 설정

```bash
cd frontend
npm install
cd ..
```

**또는 수동으로:**

```bash
# Node.js 의존성 설치
cd frontend
npm install
cd ..
```

### 4. 애플리케이션 실행

```bash
# 백엔드 실행 (새 터미널)
bash scripts/run_backend.sh

# 프론트엔드 실행 (새 터미널)
bash scripts/run_frontend.sh
```

**또는 수동으로:**

```bash
# 백엔드 실행 (새 터미널)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 프론트엔드 실행 (새 터미널)
cd frontend
npm run dev
```

### 5. 브라우저 접속

- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 📖 사용 방법

### 기본 사용법

1. 웹 브라우저에서 http://localhost:5173 접속
2. "이미지 업로드" 버튼 클릭하여 식물 사진 선택
3. 업로드 후 자동으로 분석 시작
4. 결과를 "식물의 말" 형태로 확인

### 모델 학습

```bash
# 샘플 데이터로 학습
python -m backend.app.ml.train_classifier --epochs 10 --dataset_source samples

# 사용자 데이터로 학습 (storage/samples/class_name/ 구조)
python -m backend.app.ml.train_classifier --epochs 20 --dataset_source local
```

### ONNX 모델 내보내기

```bash
bash scripts/export_onnx.sh
```

## 📁 프로젝트 구조

```
plant-whisperer/
├─ README.md                 # 이 파일
├─ .gitignore               # Git 무시 파일
├─ .env.example             # 환경 변수 예시
├─ scripts/                 # 실행 스크립트
│  ├─ setup_python_venv.sh  # Python 환경 설정
│  ├─ lock_python_deps.sh   # 의존성 고정
│  ├─ run_backend.sh        # 백엔드 실행
│  ├─ run_frontend.sh       # 프론트엔드 실행
│  └─ export_onnx.sh        # ONNX 내보내기
├─ storage/                 # 데이터 저장소
│  ├─ uploads/              # 업로드된 이미지
│  ├─ samples/              # 샘플 데이터
│  └─ models/               # 학습된 모델
├─ backend/                 # FastAPI 백엔드
│  ├─ app/
│  │  ├─ main.py           # FastAPI 엔트리
│  │  ├─ config.py         # 설정 관리
│  │  ├─ routers/          # API 라우터
│  │  ├─ services/         # 비즈니스 로직
│  │  ├─ ml/               # ML 파이프라인
│  │  └─ utils/            # 유틸리티
│  ├─ requirements.in      # Python 의존성
│  └─ requirements.txt     # 고정된 의존성
└─ frontend/               # React 프론트엔드
   ├─ src/
   │  ├─ components/       # React 컴포넌트
   │  ├─ pages/           # 페이지 컴포넌트
   │  ├─ store/           # 상태 관리
   │  └─ api/             # API 클라이언트
   ├─ package.json        # Node.js 의존성
   └─ vite.config.ts      # Vite 설정
```

## 🔧 API 엔드포인트

### 기본 API

- `GET /api/health` - 서버 상태 확인
- `POST /api/predict` - 이미지 분석 (multipart/form-data)
- `GET /api/models` - 사용 가능한 모델 목록
- `POST /api/models/select` - 서빙 모델 변경

### 학습 API

- `POST /api/train` - 모델 학습 시작
- `GET /api/train/status` - 학습 상태 확인

## 📊 성능 기준 (MVP)

- **품종 정확도**: Top-1 ≥ 80% (샘플셋 기준)
- **질병 진단**: 이진 F1 ≥ 0.85 (건강 vs 질병)
- **추론 속도**: 1장 < 1.0초 (CPU 기준, 512px 리사이즈)
- **메모리 사용**: < 2GB (모델 로딩 포함)

## 🎯 가정 및 제한사항

### 가정

- 사용자는 Python 3.11.9와 Node.js 20.x LTS를 사용
- 로컬 환경에서 실행 (클라우드 의존성 없음)
- 이미지는 일반적인 식물 사진 (배경 포함 가능)
- 기본적으로 한국어 인터페이스 사용

### 제한사항

- **라이선스**: AGPL-3.0 라이선스 모델 제외
- **데이터셋**: PlantVillage/PlantDoc 등 허용 범위 확인 후 사용
- **모델 크기**: 단일 VM에서 실행 가능한 크기로 제한
- **외부 의존성**: 유료 API 또는 클라우드 서비스 사용 금지

## 🔒 보안 및 개인정보

- 업로드된 이미지는 로컬 `storage/uploads/`에 임시 저장
- 개인정보 수집 없음 (PII 최소화)
- CORS 화이트리스트 설정 (localhost, 127.0.0.1)
- 파일 업로드 제한: 5MB, 이미지 형식만 허용

## 🧪 테스트

### 백엔드 테스트

```bash
cd backend
python -m pytest tests/ -v
```

### 프론트엔드 테스트

```bash
cd frontend
npm run test
```

### E2E 테스트

```bash
npm run test:e2e
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

### 사용된 오픈소스 라이브러리

- **FastAPI**: MIT License
- **React**: MIT License
- **PyTorch**: BSD License
- **U²-Net**: MIT License (사전학습 가중치)
- **EfficientNet**: Apache-2.0 License
- **PlantVillage Dataset**: MIT License

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 지원

- **이슈**: GitHub Issues 사용
- **문서**: 이 README와 API 문서 참조
- **커뮤니티**: GitHub Discussions 활용

## 🚀 로드맵

- [ ] 다국어 지원 (영어, 일본어)
- [ ] 모바일 앱 (React Native)
- [ ] 배치 처리 기능
- [ ] 실시간 학습 모니터링
- [ ] 모델 앙상블 지원
- [ ] 클라우드 배포 가이드

---

**Plant Whisperer** - 식물과의 대화를 시작하세요! 🌱
