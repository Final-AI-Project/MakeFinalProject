from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("DB_URL", "sqlite:///./fitness.sqlite3")

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=False,  # SQL 로그 출력 여부
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def create_db_and_tables():
    """데이터베이스 및 테이블 생성"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """세션 생성"""
    with Session(engine) as session:
        yield session

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
            print("✅ 데이터베이스 연결 성공")
            return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False
