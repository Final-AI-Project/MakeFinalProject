from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI 설정
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    DEFAULT_SPECIES: str = "몬스테라"

    # MySQL DB 설정 (ERD의 실제 DB 구조에 맞춤)
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"  # 실제 DB 사용자명으로 변경
    MYSQL_PASSWORD: str = "password"  # 실제 DB 비밀번호로 변경
    MYSQL_DB: str = "pland_db"  # 실제 DB명으로 변경

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
