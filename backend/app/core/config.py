from __future__ import annotations

from functools import lru_cache
from pydantic import Field, BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):

    # pydantic-settings v2 방식
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENV: str = Field(default='development', validation_alias='ENV')  # production, development, testing

    APP_NAME: str = Field(default='Pland API', validation_alias='APP_NAME')
    API_V1_PREFIX: str = Field(default='/api/v1', validation_alias='API_V1_PREFIX')
    VERSION: str = Field(default='0.1.0', validation_alias='VERSION')

    # JWT
    JWT_SECRET: str = Field(default='dev-only-change-me', validation_alias='JWT_SECRET')  # 개발용 기본값
    JWT_ALG: str = Field(default='HS256', validation_alias='JWT_ALG')
    ACCESS_EXPIRES: int = Field(default=900, validation_alias='ACCESS_EXPIRES')                # 15m
    REFRESH_EXPIRES: int = Field(default=60 * 60 * 24 * 7, validation_alias='REFRESH_EXPIRES') # 7d

    # Media
    MEDIA_ROOT: str = Field('media', validation_alias='MEDIA_ROOT')   # project root(pland/) 기준
    MEDIA_URL: str = Field('/media', validation_alias='MEDIA_URL')
    MAX_UPLOAD_MB: int = Field(5, validation_alias='MAX_UPLOAD_MB')

    #DB
    DB_HOST: str = Field(..., validation_alias='DB_HOST')
    DB_PORT: int = Field(3306, validation_alias='DB_PORT')
    DB_USER: str = Field(..., validation_alias='DB_USER')
    DB_PASSWORD: SecretStr = Field(..., validation_alias='DB_PASSWORD')
    DB_NAME: str = Field(..., validation_alias='DB_NAME')

    DB_POOL_SIZE: int = Field(20, validation_alias='DB_POOL_SIZE')
    DB_MAX_OVERFLOW: int = Field(0, validation_alias='DB_MAX_OVERFLOW')
    SQL_ECHO: bool = Field(False, validation_alias='SQL_ECHO')

    @property
    def ROOT_DIR(self) -> Path:
        return Path(__file__).resolve().parents[2]


@lru_cache
def get_settings() -> "Settings":
    # pylance 검사기 오류 무시 (추후 동작 확인 시 수정 예정)
    return Settings()

settings = Settings()
