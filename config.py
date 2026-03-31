import os
from functools import lru_cache


class Settings:
    APP_NAME: str = "HealthTrack"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "healthtrack-dev-secret-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = int(os.getenv("TOKEN_EXPIRE_DAYS", "7"))
    RESET_TOKEN_MAX_AGE: int = 3600

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./healthtrack.db")
    IS_VERCEL: bool = os.getenv("VERCEL", "") == "1"

    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:8080").split(",")

    DEFAULT_WATER_GOAL_ML: int = 3000
    MAX_DAILY_WATER_ML: int = 6000
    DEFAULT_CALORIE_GOAL: int = 2000
    DEFAULT_EXERCISE_GOAL: int = 30
    DEFAULT_SLEEP_GOAL: float = 8.0
    MAX_PASSWORD_LENGTH: int = 128
    MIN_PASSWORD_LENGTH: int = 8


@lru_cache()
def get_settings() -> Settings:
    return Settings()
