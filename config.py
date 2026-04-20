from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from pathlib import Path
from typing import Optional
import logging
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite:///./fund_show.db",
        description="数据库连接URL"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
        description="数据库连接池大小"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=20,
        ge=0,
        le=50,
        description="数据库连接池最大溢出数"
    )
    DATABASE_POOL_RECYCLE: int = Field(
        default=3600,
        ge=300,
        description="数据库连接回收时间(秒)"
    )
    
    APP_NAME: str = Field(
        default="海外投资基金数据服务",
        description="应用名称"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="应用版本"
    )
    APP_HOST: str = Field(
        default="0.0.0.0",
        description="应用监听地址"
    )
    APP_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="应用监听端口"
    )
    DEBUG: bool = Field(
        default=False,
        description="调试模式"
    )
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="运行环境"
    )
    
    SCHEDULER_ENABLED: bool = Field(
        default=True,
        description="是否启用定时任务"
    )
    SCHEDULER_HOUR: int = Field(
        default=4,
        ge=0,
        le=23,
        description="定时任务执行小时"
    )
    SCHEDULER_MINUTE: int = Field(
        default=0,
        ge=0,
        le=59,
        description="定时任务执行分钟"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    LOG_FILE: Optional[str] = Field(
        default=None,
        description="日志文件路径"
    )
    
    API_PREFIX: str = Field(
        default="/api/v1/funds",
        description="API路由前缀"
    )
    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="默认分页大小"
    )
    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=500,
        description="最大分页大小"
    )
    
    HOLDINGS_UPDATE_LIMIT: int = Field(
        default=50,
        ge=1,
        le=500,
        description="持仓更新时默认处理的基金数量"
    )
    FUND_LIST_DEFAULT_LIMIT: int = Field(
        default=100,
        ge=1,
        le=500,
        description="基金列表默认查询数量"
    )
    
    OVERSEAS_KEYWORDS: str = Field(
        default="QDII,QDII-ETF,海外,港股,美股,纳斯达克,标普,恒生,中概,全球,国际,境外,沪港深,香港,美国,欧洲,日本,新兴市场",
        description="海外基金关键词(逗号分隔)"
    )
    PORTFOLIO_YEAR: str = Field(
        default="2024",
        description="持仓数据年份"
    )
    QDII_SYMBOL: str = Field(
        default="QDII基金",
        description="QDII基金类型标识"
    )
    
    @property
    def overseas_keywords_list(self) -> list:
        return [k.strip() for k in self.OVERSEAS_KEYWORDS.split(',')]
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"日志级别必须是: {', '.join(valid_levels)}")
        return v_upper
    
    class Config:
        env_file = Path(__file__).parent / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    _configure_logging(settings)
    return settings


def _configure_logging(settings: Settings) -> None:
    log_level = getattr(logging, settings.LOG_LEVEL)
    
    handlers: list = [logging.StreamHandler()]
    
    if settings.LOG_FILE:
        handlers.append(logging.FileHandler(settings.LOG_FILE))
    
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        handlers=handlers
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
