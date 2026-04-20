import pytest
import logging
from repo.config import Settings, get_settings, reload_settings


class TestConfig:
    """测试配置管理"""
    
    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        assert settings.APP_HOST == "0.0.0.0"
        assert settings.APP_PORT == 8000
        assert settings.DEBUG is False
        assert settings.DATABASE_URL == "sqlite:///./fund_show.db"
    
    def test_is_sqlite_property(self):
        """测试SQLite判断属性"""
        settings = Settings(DATABASE_URL="sqlite:///test.db")
        assert settings.is_sqlite is True
        
        settings = Settings(DATABASE_URL="postgresql://user:pass@localhost/db")
        assert settings.is_sqlite is False
    
    def test_is_production_property(self):
        """测试生产环境判断属性"""
        settings = Settings(DEBUG=False)
        assert settings.is_production is True
        
        settings = Settings(DEBUG=True)
        assert settings.is_production is False
    
    def test_log_level_int_property(self):
        """测试日志级别数值属性"""
        settings = Settings(LOG_LEVEL="DEBUG")
        assert settings.log_level_int == logging.DEBUG
        
        settings = Settings(LOG_LEVEL="INFO")
        assert settings.log_level_int == logging.INFO
        
        settings = Settings(LOG_LEVEL="WARNING")
        assert settings.log_level_int == logging.WARNING
        
        settings = Settings(LOG_LEVEL="INVALID")
        assert settings.log_level_int == logging.INFO
    
    def test_get_database_settings(self):
        """测试获取数据库配置"""
        settings = Settings()
        db_settings = settings.get_database_settings()
        assert db_settings.DB_POOL_SIZE == settings.DB_POOL_SIZE
        assert db_settings.DB_MAX_OVERFLOW == settings.DB_MAX_OVERFLOW
    
    def test_get_scheduler_settings(self):
        """测试获取定时任务配置"""
        settings = Settings()
        scheduler_settings = settings.get_scheduler_settings()
        assert scheduler_settings.SCHEDULER_ENABLED == settings.SCHEDULER_ENABLED
        assert scheduler_settings.SCHEDULER_UPDATE_HOUR == settings.SCHEDULER_UPDATE_HOUR
    
    def test_get_log_settings(self):
        """测试获取日志配置"""
        settings = Settings()
        log_settings = settings.get_log_settings()
        assert log_settings.LOG_LEVEL == settings.LOG_LEVEL
        assert log_settings.LOG_FORMAT == settings.LOG_FORMAT
    
    def test_settings_singleton(self):
        """测试配置单例模式"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_reload_settings(self):
        """测试重新加载配置"""
        settings1 = get_settings()
        settings2 = reload_settings()
        assert settings1 is not settings2
