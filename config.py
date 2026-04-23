from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./fund_show.db"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    API_TITLE: str = "海外投资基金数据服务"
    API_DESCRIPTION: str = "基于akshare获取海外投资基金净值和持仓信息，提供RESTful API接口"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1/funds"
    
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_HOUR: int = 4
    SCHEDULER_MINUTE: int = 0
    SCHEDULER_JOB_ID: str = "update_fund_data"
    SCHEDULER_JOB_NAME: str = "更新基金数据任务"
    
    DEFAULT_PAGE_LIMIT: int = 100
    DEFAULT_PAGE_SKIP: int = 0
    HOLDINGS_UPDATE_LIMIT: int = 50
    
    HOLDINGS_YEAR: Optional[int] = None
    
    OVERSEAS_KEYWORDS: List[str] = [
        'QDII', 'QDII-ETF', '海外', '港股', '美股', '纳斯达克',
        '标普', '恒生', '中概', '全球', '国际', '境外', '沪港深',
        '香港', '美国', '欧洲', '日本', '新兴市场'
    ]
    
    QDII_FUND_SYMBOL: str = "QDII基金"
    
    class Config:
        env_file = Path(__file__).parent / ".env"
        case_sensitive = True
    
    def get_holdings_year(self) -> int:
        if self.HOLDINGS_YEAR is not None:
            return self.HOLDINGS_YEAR
        return datetime.now().year


@lru_cache()
def get_settings() -> Settings:
    return Settings()
