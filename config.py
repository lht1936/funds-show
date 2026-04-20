from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache
from pathlib import Path
from typing import Optional
import logging
import os

from repo.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    ENVIRONMENT: str = Field("development", pattern="^(development|testing|production)$")
    DATABASE_URL: str = Field("sqlite:///./fund_show.db")
    APP_HOST: str = Field("0.0.0.0")
    APP_PORT: int = Field(8000, ge=1, le=65535)
    DEBUG: bool = Field(False)
    LOG_LEVEL: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    SCHEDULER_ENABLED: bool = Field(True)
    SCHEDULER_FUND_UPDATE_INTERVAL_HOURS: int = Field(6, ge=1)
    SCHEDULER_NAV_UPDATE_INTERVAL_HOURS: int = Field(4, ge=1)
    SCHEDULER_HOLDINGS_UPDATE_INTERVAL_HOURS: int = Field(24, ge=1)

    FETCH_TIMEOUT: int = Field(30, ge=5)
    MAX_RETRIES: int = Field(3, ge=0, le=10)
    RETRY_DELAY_SECONDS: int = Field(1, ge=0, le=60)
    BATCH_SIZE: int = Field(10, ge=1, le=100)

    HOLDINGS_YEAR: str = Field("2024", pattern=r"^\d{4}$")
    HOLDINGS_UPDATE_MAX_FUNDS: int = Field(50, ge=1)

    QDII_FUND_SYMBOL: str = Field("QDII基金")
    DEFAULT_LIST_LIMIT: int = Field(20, ge=1)
    MAX_LIST_LIMIT: int = Field(100, ge=1)
    MAX_SERVICE_LIMIT: int = Field(1000, ge=100)

    SCHEDULER_CRON_HOUR: int = Field(4, ge=0, le=23)
    SCHEDULER_CRON_MINUTE: int = Field(0, ge=0, le=59)

    DB_POOL_SIZE: int = Field(10, ge=1)
    DB_MAX_OVERFLOW: int = Field(20, ge=0)

    OVERSEAS_KEYWORDS: str = Field("QDII,QDII-ETF,海外,港股,美股,纳斯达克,标普,恒生,中概,全球,国际,境外,沪港深,香港,美国,欧洲,日本,新兴市场")

    CORS_ORIGINS: str = Field("*")

    @property
    def overseas_keywords_list(self) -> list[str]:
        return [keyword.strip() for keyword in self.OVERSEAS_KEYWORDS.split(",") if keyword.strip()]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        allowed_schemes = ["sqlite", "postgresql", "mysql", "mariadb"]
        if not any(v.startswith(f"{scheme}://") for scheme in allowed_schemes):
            raise ConfigurationError(
                config_key="DATABASE_URL",
                message=f"数据库URL必须是以下类型之一: {', '.join(allowed_schemes)}"
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"


@lru_cache()
def get_settings() -> Settings:
    try:
        settings = Settings()
        logger.info(
            f"配置加载成功: ENVIRONMENT={settings.ENVIRONMENT}, "
            f"DEBUG={settings.DEBUG}, LOG_LEVEL={settings.LOG_LEVEL}"
        )
        return settings
    except Exception as e:
        error_msg = f"配置加载失败: {str(e)}"
        logger.critical(error_msg)
        raise ConfigurationError(
            config_key="settings",
            message=error_msg
        ) from e


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
