"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "EduHub Catalog Service"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    auth_service_url: str = "http://auth-service:8000"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
