# LLM Plant Chat Model

ERD의 diary 테이블 구조에 맞춰 채팅 내용을 저장하는 LLM 모델입니다.

## 주요 기능

- **식물과의 대화**: 일상 대화, 식물 건강 문의, 하이브리드 대화 모드 지원
- **DB 저장**: ERD의 diary 테이블에 채팅 내용 자동 저장
- **채팅 기록 조회**: 사용자별 최근 채팅 기록 조회

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DEFAULT_SPECIES=몬스테라

# MySQL DB 설정
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_db_password_here
MYSQL_DB=pland_db
```

### 3. 실행

```bash
python main.py
```

## 사용 예시

### 기본 채팅

```python
from src.orchestrator import plant_talk

result = plant_talk(
    species="호접란",
    user_text="너 잘 자라고 있지?",
    moisture=22.0
)

print(f"모드: {result.mode}")
print(f"응답: {result.reply}")
```

### DB 저장과 함께 사용

```python
from src.orchestrator import talk_for_db
from src.db import save_chat

# 채팅 데이터 생성
chat_data = talk_for_db(
    user_id="user123",
    plant_id=1,
    plant_name="우리집 호접란",
    species="호접란",
    user_content="너 잘 자라고 있지?",
    user_title="호접란과의 대화",  # 사용자가 입력한 제목 (필수)
    moisture=22.0,
    hashtag="#호접란 #일상",
    weather="맑음"
)

# DB에 저장
diary_id = await save_chat(chat_data)
print(f"저장된 일기 ID: {diary_id}")
```

### 채팅 기록 조회

```python
from src.db import get_chat_history

history = await get_chat_history("user123", limit=10)
for record in history:
    print(f"제목: {record['user_title']}")
    print(f"내용: {record['user_content']}")
    print(f"식물 응답: {record['plant_content']}")
```

## 대화 모드

1. **daily**: 일상 대화 모드
2. **plant**: 식물 건강 관련 모드
3. **hybrid**: 일상 + 식물 건강 혼합 모드

## 제목 처리

- `user_title`은 사용자가 직접 입력한 제목을 그대로 사용합니다
- 자동 생성되지 않으며, 반드시 사용자가 제공해야 합니다

## ERD 연동

이 모델은 ERD의 `diary` 테이블 구조에 맞춰 설계되었습니다:

- `user_id`: 사용자 ID
- `user_title`: 대화 제목 (자동 생성)
- `user_content`: 사용자 입력 내용
- `plant_content`: LLM 응답 내용
- `hashtag`: 해시태그 (선택사항)
- `weather`: 날씨 정보 (선택사항)
- `created_at`: 생성 시간 (자동 설정)

## 파일 구조

```
models/llm/
├── main.py              # 메인 실행 파일
├── src/
│   ├── orchestrator.py  # 대화 오케스트레이션
│   ├── chat_logic.py    # 채팅 로직
│   ├── db.py           # DB 연동
│   ├── config.py       # 설정
│   ├── rules.py        # 규칙 정의
│   ├── species_meta.py # 식물 메타데이터
│   └── utils.py        # 유틸리티
├── requirements.txt    # 의존성
└── README.md          # 이 파일
```
