from pydantic import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET: str = "secret"
    JWT_ALG: str = "HS256"
    ACCESS_EXPIRES: int = 15 * 60
    REFRESH_EXPIRES: int = 7 * 24 * 60 * 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
