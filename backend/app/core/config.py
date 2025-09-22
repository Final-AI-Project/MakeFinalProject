from __future__ import annotations

from functools import lru_cache
from typing import List
from pathlib import Path
import os

from pydantic import Field, BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parents[1]  # app 폴더
DEFAULT_ENV_FILE = APP_DIR / '.env'  # app/.env

ENV_FILE = os.getenv('PLAND_ENV_FILE', str(DEFAULT_ENV_FILE))

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE, override=False)
except Exception:
        pass


class Settings(BaseSettings):

    # pydantic-settings v2 방식
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
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
    ACCESS_EXPIRES: int = Field(default=7200, validation_alias='ACCESS_EXPIRES')               # 2h
    REFRESH_EXPIRES: int = Field(default=60 * 60 * 24 * 7, validation_alias='REFRESH_EXPIRES') # 7d

    # Media
    MEDIA_ROOT: str = Field('media', validation_alias='MEDIA_ROOT')   # project root(pland/) 기준
    MEDIA_URL: str = Field('/media', validation_alias='MEDIA_URL')
    MAX_UPLOAD_MB: int = Field(5, validation_alias='MAX_UPLOAD_MB')

    #DB - MySQL (AWS RDS용, SQLite 사용 시 선택적)
    DB_HOST: str = Field(default="", validation_alias='DB_HOST')
    DB_PORT: int = Field(default=3306, validation_alias='DB_PORT')
    DB_USER: str = Field(default="", validation_alias='DB_USER')
    DB_PASSWORD: SecretStr = Field(..., validation_alias='DB_PASSWORD')
    DB_NAME: str = Field(default="", validation_alias='DB_NAME')

    DB_POOL_SIZE: int = Field(default=20, validation_alias='DB_POOL_SIZE')
    DB_MAX_OVERFLOW: int = Field(default=0, validation_alias='DB_MAX_OVERFLOW')
    SQL_ECHO: bool = Field(default=False, validation_alias='SQL_ECHO')
    
    # SQLite 사용 여부 (개발용)
    USE_SQLITE: bool = Field(default=False, validation_alias='USE_SQLITE')
    
    # AI Model Server
    MODEL_SERVER_URL: str = Field(default='http://127.0.0.1:5000', validation_alias='MODEL_SERVER_URL')
    MODEL_SERVER_TIMEOUT: int = Field(default=30, validation_alias='MODEL_SERVER_TIMEOUT')

    # MQTT Connect
    MQTT_HOST: str = Field(default="", validation_alias='MQTT_HOST')
    MQTT_PORT: int = 8883
    MQTT_USER: str = Field(default="", validation_alias="MQTT_USER")
    MQTT_PASS: str = Field(default="", validation_alias="MQTT_PASS")
    MQTT_TOPICS: str = Field(default="", validation_alias="MQTT_TOPICS")
    MQTT_CA_PATH: str = Field(default=str((APP_DIR/"certs"/"emqxsl-ca.pem").resolve()), validation_alias="MQTT_CA_PATH",)
   

    @property
    def ROOT_DIR(self) -> Path:
        return Path(__file__).resolve().parents[2]
    
    @property
    def mqtt_topics_list(self) -> List[str]:
        return [t.strip() for t in self.MQTT_TOPICS.split(",") if t.strip()]


@lru_cache
def get_settings() -> "Settings":
    # pylance 검사기 오류 무시 (추후 동작 확인 시 수정 예정)
    return Settings()

settings = Settings()
print(f"[DB] host = '{settings.DB_HOST}'")