from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30


class SchedulerSettings(BaseSettings):
    """定时任务配置"""
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_UPDATE_HOUR: int = 4
    SCHEDULER_UPDATE_MINUTE: int = 0
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"


class LogSettings(BaseSettings):
    """日志配置"""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5


class DataFetchSettings(BaseSettings):
    """数据获取配置"""
    # 重试配置
    DATA_FETCH_MAX_RETRIES: int = 3
    DATA_FETCH_RETRY_DELAY: float = 1.0
    DATA_FETCH_TIMEOUT: int = 30
    
    # 批处理配置
    DATA_FETCH_BATCH_SIZE: int = 50
    DATA_FETCH_BATCH_DELAY: float = 0.5
    
    # 持仓更新配置
    DATA_FETCH_HOLDINGS_DEFAULT_LIMIT: int = 50
    DATA_FETCH_HOLDINGS_DEFAULT_YEAR: str = "2024"
    
    # 海外基金关键词
    OVERSEAS_FUND_KEYWORDS: List[str] = [
        'QDII', 'QDII-ETF', '海外', '港股', '美股', '纳斯达克', 
        '标普', '恒生', '中概', '全球', '国际', '境外', '沪港深',
        '香港', '美国', '欧洲', '日本', '新兴市场'
    ]
    
    # API 数据源配置
    QDII_FUND_SYMBOL: str = "QDII基金"
    
    # 慢查询阈值（秒）
    SLOW_QUERY_THRESHOLD: float = 1.0


class APISettings(BaseSettings):
    """API配置"""
    API_PREFIX: str = "/api/v1"
    API_CORS_ORIGINS: List[str] = ["*"]
    
    # 分页默认值
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    DEFAULT_SKIP: int = 0


class Settings(BaseSettings):
    """应用主配置类"""
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # 应用基础配置
    APP_NAME: str = "海外投资基金数据服务"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./fund_show.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30
    
    # 定时任务配置
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_UPDATE_HOUR: int = 4
    SCHEDULER_UPDATE_MINUTE: int = 0
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # 数据获取配置
    DATA_FETCH_MAX_RETRIES: int = 3
    DATA_FETCH_RETRY_DELAY: float = 1.0
    DATA_FETCH_TIMEOUT: int = 30
    DATA_FETCH_BATCH_SIZE: int = 50
    DATA_FETCH_BATCH_DELAY: float = 0.5
    DATA_FETCH_HOLDINGS_DEFAULT_LIMIT: int = 50
    DATA_FETCH_HOLDINGS_DEFAULT_YEAR: str = "2024"
    
    # 海外基金关键词
    OVERSEAS_FUND_KEYWORDS: List[str] = [
        'QDII', 'QDII-ETF', '海外', '港股', '美股', '纳斯达克', 
        '标普', '恒生', '中概', '全球', '国际', '境外', '沪港深',
        '香港', '美国', '欧洲', '日本', '新兴市场'
    ]
    
    # API 数据源配置
    QDII_FUND_SYMBOL: str = "QDII基金"
    SLOW_QUERY_THRESHOLD: float = 1.0
    
    # API配置
    API_PREFIX: str = "/api/v1"
    API_CORS_ORIGINS: List[str] = ["*"]
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    DEFAULT_SKIP: int = 0
    
    @property
    def is_sqlite(self) -> bool:
        """是否使用SQLite数据库"""
        return self.DATABASE_URL.startswith("sqlite")
    
    @property
    def is_production(self) -> bool:
        """是否生产环境"""
        return not self.DEBUG
    
    @property
    def log_level_int(self) -> int:
        """获取日志级别数值"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(self.LOG_LEVEL.upper(), logging.INFO)
    
    def get_database_settings(self) -> DatabaseSettings:
        """获取数据库配置对象"""
        return DatabaseSettings(
            DB_POOL_SIZE=self.DB_POOL_SIZE,
            DB_MAX_OVERFLOW=self.DB_MAX_OVERFLOW,
            DB_POOL_RECYCLE=self.DB_POOL_RECYCLE,
            DB_POOL_TIMEOUT=self.DB_POOL_TIMEOUT,
        )
    
    def get_scheduler_settings(self) -> SchedulerSettings:
        """获取定时任务配置对象"""
        return SchedulerSettings(
            SCHEDULER_ENABLED=self.SCHEDULER_ENABLED,
            SCHEDULER_UPDATE_HOUR=self.SCHEDULER_UPDATE_HOUR,
            SCHEDULER_UPDATE_MINUTE=self.SCHEDULER_UPDATE_MINUTE,
            SCHEDULER_TIMEZONE=self.SCHEDULER_TIMEZONE,
        )
    
    def get_log_settings(self) -> LogSettings:
        """获取日志配置对象"""
        return LogSettings(
            LOG_LEVEL=self.LOG_LEVEL,
            LOG_FORMAT=self.LOG_FORMAT,
            LOG_FILE=self.LOG_FILE,
            LOG_MAX_BYTES=10 * 1024 * 1024,
            LOG_BACKUP_COUNT=5,
        )
    
    def get_data_fetch_settings(self) -> DataFetchSettings:
        """获取数据获取配置对象"""
        return DataFetchSettings(
            DATA_FETCH_MAX_RETRIES=self.DATA_FETCH_MAX_RETRIES,
            DATA_FETCH_RETRY_DELAY=self.DATA_FETCH_RETRY_DELAY,
            DATA_FETCH_TIMEOUT=self.DATA_FETCH_TIMEOUT,
            DATA_FETCH_BATCH_SIZE=self.DATA_FETCH_BATCH_SIZE,
            DATA_FETCH_BATCH_DELAY=self.DATA_FETCH_BATCH_DELAY,
            DATA_FETCH_HOLDINGS_DEFAULT_LIMIT=self.DATA_FETCH_HOLDINGS_DEFAULT_LIMIT,
            DATA_FETCH_HOLDINGS_DEFAULT_YEAR=self.DATA_FETCH_HOLDINGS_DEFAULT_YEAR,
            OVERSEAS_FUND_KEYWORDS=self.OVERSEAS_FUND_KEYWORDS,
            QDII_FUND_SYMBOL=self.QDII_FUND_SYMBOL,
            SLOW_QUERY_THRESHOLD=self.SLOW_QUERY_THRESHOLD,
        )
    
    def get_api_settings(self) -> APISettings:
        """获取API配置对象"""
        return APISettings(
            API_PREFIX=self.API_PREFIX,
            API_CORS_ORIGINS=self.API_CORS_ORIGINS,
            DEFAULT_PAGE_SIZE=self.DEFAULT_PAGE_SIZE,
            MAX_PAGE_SIZE=self.MAX_PAGE_SIZE,
            DEFAULT_SKIP=self.DEFAULT_SKIP,
        )


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    try:
        settings = Settings()
        logger.info(f"配置加载成功: DEBUG={settings.DEBUG}")
        return settings
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        raise


def reload_settings() -> Settings:
    """重新加载配置"""
    get_settings.cache_clear()
    return get_settings()
