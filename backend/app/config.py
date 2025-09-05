from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# class Settings(BaseSettings):
#     APP_NAME: str = "Pland API"
#     API_V1_STR: str = "/api/v1" # api 버저닝 
#     VERSION: str = "0.1.0"

#     #JWT 토큰 설정
#     JWT_SECRET: str = Field(..., validation_alias="JWT_SECRET")
#     JWT_ALG: str = Field("HS256", validation_alias="JWT_ALG")
#     ACCESS_EXPIRES: int = Field(900, validation_alias="ACCESS_EXPIRES") # 900초 (15분)
#     REFRESH_EXPIRES: int = Field(60 * 60 * 24 * 7, validation_alias="REFRESH_EXPIRES") # 60 * 60 * 24 * 7초 (1주일)

#     model_config = SettingsConfigDict(
#         env_file=Path(".env"),
#         env_file_encoding="utf-8",
#         case_sensitive=True,
#         extra="ignore",
#     )

class Settings(BaseSettings):
    # App meta
    APP_NAME: str = Field(default="Pland API", env="APP_NAME")
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    VERSION: str = Field(default="0.1.0", env="VERSION")

    # JWT
    JWT_SECRET: str = Field(default="dev-only-change-me", env="JWT_SECRET")  # 개발용 기본값
    JWT_ALG: str = Field(default="HS256", env="JWT_ALG")
    ACCESS_EXPIRES: int = Field(default=900, env="ACCESS_EXPIRES")                # 15m
    REFRESH_EXPIRES: int = Field(default=60 * 60 * 24 * 7, env="REFRESH_EXPIRES") # 7d

    # pydantic-settings v2 방식
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )



@lru_cache
def get_settings() -> "Settings":
    # pylance 검사기 오류 무시 (추후 동작 확인 시 수정 예정)
    return Settings()