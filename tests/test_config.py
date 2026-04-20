import pytest
from repo.config import Settings, Environment, get_settings, clear_settings_cache


class TestConfig:
    
    def test_default_settings(self):
        clear_settings_cache()
        settings = get_settings()
        
        assert settings.DATABASE_URL == "sqlite:///./fund_show.db"
        assert settings.APP_HOST == "0.0.0.0"
        assert settings.APP_PORT == 8000
        assert settings.DEBUG is False
        assert settings.ENVIRONMENT == Environment.DEVELOPMENT
    
    def test_api_settings(self):
        clear_settings_cache()
        settings = get_settings()
        
        assert settings.API_PREFIX == "/api/v1/funds"
        assert settings.DEFAULT_PAGE_SIZE == 20
        assert settings.MAX_PAGE_SIZE == 100
    
    def test_data_fetch_settings(self):
        clear_settings_cache()
        settings = get_settings()
        
        assert settings.HOLDINGS_UPDATE_LIMIT == 50
        assert settings.FUND_LIST_DEFAULT_LIMIT == 100
        assert settings.PORTFOLIO_YEAR == "2024"
        assert settings.QDII_SYMBOL == "QDII基金"
    
    def test_overseas_keywords(self):
        clear_settings_cache()
        settings = get_settings()
        
        keywords = settings.overseas_keywords_list
        assert isinstance(keywords, list)
        assert "QDII" in keywords
        assert "海外" in keywords
        assert len(keywords) > 0
    
    def test_environment_properties(self):
        clear_settings_cache()
        settings = get_settings()
        
        assert settings.is_development is True
        assert settings.is_production is False
    
    def test_log_level_validation(self):
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            from repo.config import LogSettings
            LogSettings(LOG_LEVEL="INVALID")
    
    def test_valid_log_levels(self):
        from repo.config import LogSettings
        
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            log_settings = LogSettings(LOG_LEVEL=level)
            assert log_settings.LOG_LEVEL == level
    
    def test_settings_cache(self):
        clear_settings_cache()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
        
        clear_settings_cache()
        settings3 = get_settings()
        assert settings1 is not settings3
