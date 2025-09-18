from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # DB
    db_host: str = Field(default="127.0.0.1", env="DB_HOST")
    db_port: int = Field(default=3306, env="DB_PORT")
    db_user: str = Field(default="root", env="DB_USER")
    db_pass: str = Field(default="", env="DB_PASS")
    db_name: str = Field(default="plantcare", env="DB_NAME")

    # WEATHER
    weather_provider: str = Field(default="FAKE", env="WEATHER_PROVIDER")
    kma_api_key: str = Field(default="", env="KMA_API_KEY")
    kma_hours: int = Field(default=8, env="KMA_HOURS")

    fake_forecast_csv: str = Field(default="./data/raw/forecast_sample.csv", env="FAKE_FORECAST_CSV")

    # GEOCODER
    geocoder_primary: str = Field(default="KAKAO", env="GEOCODER_PRIMARY")     # KAKAO | GOOGLE | NOMINATIM
    geocoder_region: str = Field(default="KR", env="GEOCODER_REGION")
    geocoder_language: str = Field(default="ko", env="GEOCODER_LANGUAGE")

    google_maps_api_key: str = Field(default="", env="GOOGLE_MAPS_API_KEY")
    kakao_rest_api_key: str = Field(default="", env="KAKAO_REST_API_KEY")
    naver_client_id: str = Field(default="", env="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(default="", env="NAVER_CLIENT_SECRET")
    nominatim_base: str = Field(default="https://nominatim.openstreetmap.org", env="NOMINATIM_BASE")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
