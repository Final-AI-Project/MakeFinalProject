"""
Plant Whisperer Configuration
애플리케이션 설정 관리
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Backend Configuration
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    backend_workers: int = 1
    backend_reload: bool = True
    
    # Frontend Configuration
    frontend_host: str = "127.0.0.1"
    frontend_port: int = 5173
    
    # API Configuration
    api_base_url: str = "http://localhost:8000"
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Storage Configuration
    storage_path: str = "./storage"
    upload_max_size: int = 5242880  # 5MB in bytes
    upload_allowed_extensions: List[str] = ["jpg", "jpeg", "png", "webp"]
    
    # ML Configuration
    model_cache_dir: str = "./storage/models"
    sample_data_dir: str = "./storage/samples"
    default_model_name: str = "efficientnet_b0"
    
    # Inference Configuration
    inference_device: str = "cpu"  # cpu, cuda
    inference_batch_size: int = 1
    inference_image_size: int = 512
    inference_confidence_threshold: float = 0.5
    inference_timeout: int = 120  # 2분으로 증가
    
    # Training Configuration
    training_epochs: int = 10
    training_batch_size: int = 32
    training_learning_rate: float = 0.001
    training_validation_split: float = 0.2
    training_random_seed: int = 42
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/plant_whisperer.log"
    
    # Security Configuration
    secret_key: str = "your-secret-key-here-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Optional: Local LLM Configuration (disabled by default)
    use_local_llm: bool = False
    local_llm_model_path: str = "./storage/models/qwen2-1.5b-instruct.gguf"
    local_llm_max_tokens: int = 512
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """CORS origins 파싱"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v
    
    @validator("upload_allowed_extensions", pre=True)
    def parse_upload_extensions(cls, v):
        """업로드 허용 확장자 파싱"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        protected_namespaces = ('settings_',)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return settings
