from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    DEFAULT_SPECIES: str = "몬스테라"

    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "plant_user"
    MYSQL_PASSWORD: str = "plant_pass"
    MYSQL_DB: str = "plantchat"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
