from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FinRef"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()