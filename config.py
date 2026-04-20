from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./fund_show.db"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    class Config:
        env_file = Path(__file__).parent / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
