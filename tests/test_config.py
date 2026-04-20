import pytest
from pydantic import ValidationError

from repo.config import Settings, get_settings, reload_settings


class TestConfig:
    def test_default_settings(self):
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.DATABASE_URL == "sqlite:///./fund_show.db"
        assert settings.APP_PORT == 8000
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"

    def test_environment_validation(self):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="invalid")

    def test_port_validation(self):
        with pytest.raises(ValidationError):
            Settings(APP_PORT=0)
        with pytest.raises(ValidationError):
            Settings(APP_PORT=65536)

    def test_log_level_validation(self):
        with pytest.raises(ValidationError):
            Settings(LOG_LEVEL="INVALID")

    def test_cors_origins_list_single(self):
        settings = Settings(CORS_ORIGINS="*")
        assert settings.cors_origins_list == ["*"]

    def test_cors_origins_list_multiple(self):
        origins = "http://localhost:3000,http://example.com"
        settings = Settings(CORS_ORIGINS=origins)
        assert len(settings.cors_origins_list) == 2
        assert "http://localhost:3000" in settings.cors_origins_list
        assert "http://example.com" in settings.cors_origins_list

    def test_environment_flags(self):
        settings = Settings(ENVIRONMENT="development")
        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_testing is False

        settings = Settings(ENVIRONMENT="production")
        assert settings.is_production is True

        settings = Settings(ENVIRONMENT="testing")
        assert settings.is_testing is True

    def test_get_settings_caching(self):
        reload_settings()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_reload_settings(self):
        reload_settings()
        s1 = get_settings()
        s2 = reload_settings()
        assert s1 is not s2
