현재 생각 중인 백엔트 리드미 파일입니다.

---

프로젝트 폴더 구조

pland/
├─ README.md # 이 파일
├─ .gitignore # Git 무시 파일
├─ .env # 환경 변수 예시
├─ requirements.txt # 고정된 의존성
├─ models/ # 탐지기, 분류기 파일
│ ├─ weight/ # 가중치
│ ├─ LMM/ # 자연어 모델
│ ├─ classifier/ # 분류 모델
│ └─ detector/ # 탐지 모델
├─ backend/ # FastAPI 백엔드
│ └─ app/
│ ├─ main.py # FastAPI 엔트리
│ ├─ config.py # 설정 관리
│ ├─ routers/ # API 라우터
│ ├─ services/ # 비즈니스 로직
│ ├─ ml/ # ML 파이프라인
│ └─ utils/ # 유틸리티(ex. token)
└───────────────────────────────────────────────

- frontend/

DB - SQLite or MongoDB or MySQL
